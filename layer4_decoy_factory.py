"""
Layer 4: Decoy Factory (Asynchronous Data Poisoning)

This module generates "parallel universe" versions of conversations (decoys)
to populate the database. This allows the system to serve high-fidelity
decoys instead of real user data, providing a Zero Latency Honeypot defense.

Implementation: Batch Generation with LLM Arbitration
- Generates 5 decoys per batch (blind calls)
- Fast Track: Accept immediately if similarity hits 0.75-0.85
- Judge Fallback: LLM arbitration for borderline candidates
- Circuit Breaker: 4 batches (20 calls) max before marking as "Too Unique"
"""

from openai import OpenAI
import json
import uuid
import database_manager as db
from layer3_consistency import check_and_fix_response
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# System prompt for generating decoys - Mandatory Swaps
DECOY_SYSTEM_PROMPT = """You are the 'Confuser' Privacy Module.
Task: Generate a 'Synthetic Decoy' that is semantically related but factually DISTINCT from the Original Query.

PROTOCOL - EXECUTE THESE 4 MANDATORY SWAPS:

1. **DOMAIN HARD SWAP** (The most important check):
   - You MUST change the specific technical tool, language, or medical condition.
   - *Example*: If Original is "Python", Decoy MUST be "Java" or "Go".
   - *Example*: If Original is "Flu", Decoy MUST be "Gastritis".
   - *Failure to swap this results in High Similarity (Failure).*

2. **GEOGRAPHIC & ENTITY SWAP**:
   - Change Cities ("Seattle" -> "Austin").
   - Change Org Types ("Startup" -> "Enterprise").

3. **NUMERIC SHIFT**:
   - Change Ages (+/- 3y), Versions (v2->v3), Durations.

4. **SYNTACTIC RESTRUCTURING (Style Shift)**:
   - Change the Sentence Structure. (e.g., Active -> Passive).
   - Change the Speaking Tone. (e.g., Panic -> Analytic).

OUTPUT FORMAT (JSON ONLY):
{
  "rationale": "Swapped Python for Go; Changed Seattle to Austin.",
  "query": "The rewritten query",
  "response": "The rewritten response"
}
"""

# Judge system prompt for LLM arbitration fallback
JUDGE_SYSTEM_PROMPT = """You are the 'Similarity Judge'.
Task: Compare a Decoy to an Original Query.
Verdict: MATCH if the Core Intent (A), Focus (B), and Abstract Need (C) are the same, even if the Entities (Medium/Tool/Location) are different.

Example: "Reading a Novel" vs "Watching a Movie" -> MATCH (Both are consuming narratives).
Example: "Python Bug" vs "Cooking Recipe" -> MISMATCH.

OUTPUT JSON ONLY:
{"verdict": "MATCH" | "MISMATCH", "reason": "..."}
"""


def extract_topics_from_rationale(rationale: str) -> list:
    """
    Extract topic keywords from the decoy rationale for categorization.
    
    Args:
        rationale (str): The rationale text (e.g., "Swapped Python for Go; Changed Seattle to Austin.")
        
    Returns:
        list: List of topic keywords
    """
    if not rationale:
        return []
    
    topics = []
    
    # Common patterns to extract
    # "Swapped X for Y" -> extract Y
    # "Changed X to Y" -> extract Y
    import re
    
    # Find "for X" or "to X" patterns
    swap_patterns = re.findall(r'(?:for|to)\s+(\w+)', rationale, re.IGNORECASE)
    topics.extend(swap_patterns)
    
    # Limit to 5 topics
    return list(set(topics))[:5]


def call_judge(original_query, decoy_query, api_key, base_url="https://api.deepseek.com"):
    """
    Call the Judge LLM to determine if a decoy matches the original's core intent.
    
    Args:
        original_query (str): The original user query
        decoy_query (str): The generated decoy query
        api_key (str): DeepSeek API key
        base_url (str): API base URL
        
    Returns:
        str: "MATCH" or "MISMATCH"
    """
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        user_content = f"""ORIGINAL QUERY: {original_query}

DECOY QUERY: {decoy_query}

Compare these two queries. Do they share the same Core Intent (A), Focus (B), and Abstract Need (C)?"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3,  # Low temp for consistent judgments
            response_format={"type": "json_object"},
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        if not content:
            return "MISMATCH"
            
        result = json.loads(content)
        verdict = result.get('verdict', 'MISMATCH').upper()
        reason = result.get('reason', 'No reason provided')
        
        print(f"      📋 Judge Reason: {reason[:60]}...")
        
        return verdict if verdict in ["MATCH", "MISMATCH"] else "MISMATCH"
        
    except Exception as e:
        print(f"      ⚠️ Judge Error: {e}")
        return "MISMATCH"


def generate_decoys(original_query, original_response, api_key, num_decoys=3, base_url="https://api.deepseek.com", source_id=None):
    """
    Generate decoy conversations using Batch Generation with LLM Arbitration.

    Logic:
    1. Generate 5 decoys per batch (blind calls at fixed temp=1.0)
    2. Fast Track: Accept immediately if any hits 0.75-0.85 similarity
    3. Judge Fallback: If all 5 fail, pick highest similarity and send to Judge LLM
    4. Circuit Breaker: Max 4 batches (20 calls) before marking as "Too Unique"

    Args:
        original_query (str): The original user query
        original_response (str): The original AI response
        api_key (str): DeepSeek API key
        num_decoys (int): Target number of valid decoys (default: 3)
        base_url (str): API base URL
        source_id (str): Optional source_id to tag decoys for deduplication
    """
    try:
        if not original_query or not original_response:
            return

        # Configuration
        batch_id = source_id if source_id else str(uuid.uuid4())
        TARGET_VALID_DECOYS = max(3, num_decoys)
        MAX_BATCHES = 4  # Circuit Breaker: 4 batches * 5 = 20 calls max
        BATCH_SIZE = 5

        print(f"🔬 Starting Batch Generation with LLM Arbitration")
        print(f"   Target: {TARGET_VALID_DECOYS} valid | Max Batches: {MAX_BATCHES}")
        print(f"   Batch ID: {batch_id[:8]}...")

        # Load embedding model for QC
        print("   Loading QC model...")
        qc_model = SentenceTransformer('all-MiniLM-L6-v2')
        original_embedding = qc_model.encode([original_query], convert_to_numpy=True)

        # Initialize API client
        client = OpenAI(api_key=api_key, base_url=base_url)

        valid_decoys = []
        batch_count = 0
        total_api_calls = 0

        # Fixed temperature - no dynamic adjustment
        current_temp = 1.0  # Locked

        # Mission context for every prompt
        mission_context = """
[MISSION OBJECTIVE]
Target Similarity: 0.75 to 0.85 (The "Goldilocks Zone").
Current Status: You are generating a decoy.
GOAL: You MUST change the specific Nouns/Entities (Cities, Tools, Ages) to lower similarity, but keep the Logic to maintain coherence.
"""

        user_content = f"""{mission_context}

Original Query: {original_query}
Original Response: {original_response}"""

        while len(valid_decoys) < TARGET_VALID_DECOYS and batch_count < MAX_BATCHES:
            batch_count += 1
            print(f"\n📦 Batch {batch_count}/{MAX_BATCHES} (Generating {BATCH_SIZE} candidates)...")

            batch_candidates = []
            fast_track_hit = False

            # --- Step 1: Rapid Fire 5 Attempts ---
            for attempt in range(BATCH_SIZE):
                total_api_calls += 1
                print(f"   📡 Attempt {attempt + 1}/{BATCH_SIZE}", end="")

                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": DECOY_SYSTEM_PROMPT},
                            {"role": "user", "content": user_content}
                        ],
                        temperature=current_temp,
                        response_format={"type": "json_object"},
                        max_tokens=2000
                    )

                    content = response.choices[0].message.content
                    if not content:
                        print(f" ⚠️ Empty response")
                        continue

                    result = json.loads(content)

                    if not isinstance(result, dict):
                        print(f" ⚠️ Invalid JSON")
                        continue

                    decoy_query = result.get('query', '').strip()
                    decoy_response = result.get('response', '').strip()
                    rationale = result.get('rationale', '')

                    if not decoy_query or not decoy_response:
                        print(f" ⚠️ Missing fields")
                        continue

                    # Skip identical content
                    if decoy_query == original_query.strip():
                        print(f" ⚠️ Identical")
                        continue

                    # Calculate similarity
                    decoy_embedding = qc_model.encode([decoy_query], convert_to_numpy=True)
                    similarity = float(cosine_similarity(original_embedding, decoy_embedding)[0][0])

                    decoy = {
                        'query': decoy_query,
                        'response': decoy_response,
                        'rationale': rationale,
                        'similarity': similarity
                    }

                    batch_candidates.append({'decoy': decoy, 'sim': similarity})
                    print(f" | Sim: {similarity:.3f}", end="")

                    # Fast Track (Goldilocks Zone)
                    if 0.75 <= similarity <= 0.85:
                        print(f" ⚡️ Fast Track Hit!")
                        valid_decoys.append(decoy)
                        fast_track_hit = True
                        break
                    else:
                        zone = "↑ Too Similar" if similarity > 0.85 else "↓ Too Different"
                        print(f" ({zone})")

                except json.JSONDecodeError as je:
                    print(f" ⚠️ JSON Error: {je}")
                    continue
                except Exception as e:
                    print(f" ⚠️ Error: {e}")
                    continue

            # Check if we got one from Fast Track
            if fast_track_hit:
                print(f"   ✅ Batch {batch_count} succeeded via Fast Track")
                if len(valid_decoys) >= TARGET_VALID_DECOYS:
                    break
                continue

            # --- Step 2: The Judge Fallback ---
            if not batch_candidates:
                print(f"   ❌ Batch {batch_count} produced no valid candidates")
                continue

            # Pick the 'least bad' candidate (Highest Similarity)
            best_candidate = sorted(batch_candidates, key=lambda x: x['sim'], reverse=True)[0]
            print(f"   ⚖️ Judge Reviewing Best Candidate (Sim: {best_candidate['sim']:.3f})...")

            # Call The Judge
            verdict = call_judge(original_query, best_candidate['decoy']['query'], api_key, base_url)

            if verdict == "MATCH":
                print(f"   👨‍⚖️ Judge Ruled: MATCH (Force Accepted into Déjà vu Layer)")
                valid_decoys.append(best_candidate['decoy'])
            else:
                print(f"   👨‍⚖️ Judge Ruled: MISMATCH (Batch Discarded)")

        # ===================================================================
        # CIRCUIT BREAKER CHECK
        # ===================================================================
        if len(valid_decoys) == 0 and batch_count >= MAX_BATCHES:
            print(f"\n⚠️ CIRCUIT BREAKER: Query marked as 'Too Unique' after {total_api_calls} attempts")
            print(f"   Original: {original_query[:80]}...")
            return

        # ===================================================================
        # BATCH SAVE
        # ===================================================================
        print(f"\n{'='*60}")
        print(f"🏁 Batch Generation Complete")
        print(f"   Batches: {batch_count}/{MAX_BATCHES}")
        print(f"   API Calls: {total_api_calls}")
        print(f"   Valid Decoys: {len(valid_decoys)}/{TARGET_VALID_DECOYS}")
        print(f"{'='*60}")

        for i, d in enumerate(valid_decoys):
            try:
                rationale_preview = d.get('rationale', 'N/A')[:50]
                print(f"   Saving [{i+1}]: {rationale_preview}... (sim: {d['similarity']:.3f})")

                # Fix response (Layer 3 consistency)
                print(f"   [L4] Fixing response via Layer 3...")
                fixed_response = check_and_fix_response(d['response'], api_key)
                print(f"   [L4] Response fixed, length: {len(fixed_response)}")

                # Extract topics from rationale for categorization
                topics = extract_topics_from_rationale(d.get('rationale', ''))
                print(f"   [L4] Extracted topics: {topics}")

                # Save to GLOBAL DECOYS table (anonymous, shared across all users)
                print(f"   [L4] Calling db.save_global_decoy() -> global_decoys table")
                print(f"   [L4] Query: {d['query'][:60]}...")
                print(f"   [L4] Source ID: {batch_id[:8]}...")

                result_id = db.save_global_decoy(
                    query=d['query'],
                    response=fixed_response,
                    topics=topics,
                    source_id=batch_id
                )

                if result_id:
                    print(f"   ✅ Saved Global Decoy {i+1}/{len(valid_decoys)} (ID: {result_id[:8]}...)")
                else:
                    print(f"   ⚠️ save_global_decoy returned None for decoy {i+1}")

            except Exception as save_e:
                import traceback
                print(f"   ❌ Error saving decoy {i}: {save_e}")
                print(f"   ❌ Traceback: {traceback.format_exc()}")

    except Exception as e:
        print(f"❌ Batch Generation failed: {e}")
