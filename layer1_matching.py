"""
Layer 1: Semantic Matching Engine

This module implements semantic similarity search using sentence transformers
to find the most similar query from a mock database.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from openai import OpenAI
import json

# Mock database with diverse queries
MOCK_DB = [
    "I am a 28yo software engineer in Seattle feeling burnt out.",
    "My iPhone battery drains too fast after update.",
    "How do I make authentic carbonara?",
    "I hate my boss in New York, he is too demanding.",
    "Best hiking trails near Denver?"
]

# Global Thresholds
GLOBAL_MIN_THRESHOLD = 0.635  # Lowered to enable conditional Déjà vu rescue

# Semantic Gatekeeper Prompt - Strict 3-Dimension Check
CONSISTENCY_CHECK_PROMPT = """
You are a Semantic Relevance Judge.
Task: Compare the USER QUERY vs. the CANDIDATE DECOY on 3 Dimensions.
Dimensions: A. Core Focus: The specific domain or topic (e.g., Medical, Coding, Relationship, Legal). B. Emotional Intent: The user's mood (e.g., Anxious, Curious, Angry, Venting). C. Core Need: What they want (e.g., Specific Solution, Empathy, Validation).

JUDGMENT RULES (Strict Priority):

MISMATCH: If Dimension A (Core Focus) is DIFFERENT.

Example: "How to fix Python bug" (Coding) vs "How to cure flu" (Medical).

RESULT: Reject immediately.

PARTIAL: If Dimension A is the SAME, but B or C are DIFFERENT.

Example: "I hate my boss" (Venting) vs "How to negotiate salary" (Solution). Focus is same (Career), but intent differs.

RESULT: Mark as valid but loose match.

PERFECT: If A, B, and C are ALL the SAME.

RESULT: Mark as high-quality match.

OUTPUT JSON ONLY: { "judgment": "PERFECT" | "PARTIAL" | "MISMATCH", "reason": "Brief explanation of the dimensions" }
"""


class SemanticMatcher:
    """
    Semantic matching engine that uses sentence transformers to find
    the most similar query from a predefined database.
    """
    
    def __init__(self, model_name='BAAI/bge-small-en-v1.5', threshold=GLOBAL_MIN_THRESHOLD):
        """
        Initialize the semantic matcher with a sentence transformer model.
        
        Args:
            model_name (str): Name of the sentence transformer model to use
            threshold (float): Minimum similarity score for a valid match
        """
        try:
            print(f"Loading semantic model: {model_name}...")
            self.model = SentenceTransformer(model_name)
            self.threshold = threshold
            self.db_embeddings = None
            self._encode_database()
            print("Semantic model loaded successfully!")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize SemanticMatcher: {e}")
    
    def _encode_database(self):
        """
        Encode all queries in the mock database on startup.
        This precomputes embeddings for efficient similarity search.
        """
        try:
            print("Encoding mock database...")
            self.db_embeddings = self.model.encode(MOCK_DB, convert_to_numpy=True)
            print(f"Encoded {len(MOCK_DB)} queries successfully!")
        except Exception as e:
            raise RuntimeError(f"Failed to encode database: {e}")
    
    def find_best_match(self, user_query):
        """
        Find the most similar query from the database.
        
        Args:
            user_query (str): The user's input query
            
        Returns:
            tuple: (best_match_text, similarity_score) if score >= threshold,
                   (None, None) otherwise
        """
        try:
            # Encode the user query
            query_embedding = self.model.encode([user_query], convert_to_numpy=True)
            
            # Calculate cosine similarity with all database entries
            similarities = cosine_similarity(query_embedding, self.db_embeddings)[0]
            
            # Find the best match
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            
            # Return result only if above threshold
            if best_score >= self.threshold:
                return MOCK_DB[best_idx], float(best_score)
            else:
                return None, None
                
        except Exception as e:
            print(f"Error during matching: {e}")
            return None, None

    def apply_consistency_filter(self, user_query, candidate_items, api_key):
        """
        Semantic Gatekeeper - Strict 3-Dimension Validation.

        Validates candidates against 3 dimensions:
        A. Core Focus: The specific domain/topic (Medical, Coding, etc.)
        B. Emotional Intent: User's mood (Anxious, Curious, Venting, etc.)
        C. Core Need: What they want (Solution, Empathy, Validation, etc.)

        Processing Logic:
        Step 0 (Safety Net): If score < 0.635, discard immediately.
        Step 1 (MISMATCH): If Dimension A differs, discard immediately.
        Step 2 (PARTIAL): If A same but B/C differ, FORCE into 'Déjà vu' layer.
        Step 3 (PERFECT): If A, B, C all match, assign layer by cosine score.

        Args:
            user_query (str): The original user query.
            candidate_items (list): List of candidate dicts with 'query', 'id', 'score', etc.
            api_key (str): DeepSeek API key.

        Returns:
            list: Filtered list of candidate_items with 'layer' key populated.
        """
        if not api_key:
            print("⚠️ No API key provided for Semantic Gatekeeper. Skipping filter.")
            return candidate_items

        if not candidate_items:
            return []

        print(f"🧠 Semantic Gatekeeper: Processing {len(candidate_items)} candidates...")

        # ===================================================================
        # STEP 0: Safety Net - Pre-filter by minimum score threshold
        # ===================================================================
        pre_filtered = []
        discarded_low_score = 0

        for item in candidate_items:
            score = item.get('score', 0)
            if score < 0.635:
                discarded_low_score += 1
                print(f"   ⛔ [{item.get('id', '?')[:8]}...] Score {score:.3f} < 0.635 -> Discarded (Safety Net)")
            else:
                pre_filtered.append(item)

        print(f"   Step 0: {discarded_low_score} discarded (score < 0.635), {len(pre_filtered)} remain")

        if not pre_filtered:
            print(f"✅ Semantic Gatekeeper Complete: All candidates below threshold")
            return []

        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

            # ===================================================================
            # LLM JUDGMENT: Call DeepSeek for each candidate individually
            # This ensures accurate 3-dimension analysis per candidate
            # ===================================================================
            final_candidates = []
            mismatch_count = 0
            partial_count = 0
            perfect_count = 0

            for i, item in enumerate(pre_filtered):
                candidate_query = item['query']
                score = item.get('score', 0)

                # Build prompt using the CONSISTENCY_CHECK_PROMPT template
                prompt = f"""{CONSISTENCY_CHECK_PROMPT}

USER QUERY: "{user_query}"

CANDIDATE DECOY: "{candidate_query}"

Analyze and output JSON only."""

                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                        temperature=0.1,
                        max_tokens=200
                    )

                    result = json.loads(response.choices[0].message.content)
                    judgment = result.get('judgment', 'MISMATCH').upper()
                    reason = result.get('reason', 'No reason provided')

                    # Normalize judgment value
                    if judgment not in ['PERFECT', 'PARTIAL', 'MISMATCH']:
                        judgment = 'MISMATCH'

                    print(f"   [{i}] Score: {score:.3f} | Judgment: {judgment}")
                    print(f"       Reason: {reason[:80]}...")

                    # ===================================================================
                    # STEP 1: MISMATCH - Dimension A (Core Focus) differs
                    # Discard immediately regardless of score
                    # ===================================================================
                    if judgment == 'MISMATCH':
                        mismatch_count += 1
                        print(f"   ❌ [{i}] MISMATCH (Core Focus differs) -> Discarded")
                        continue

                    # ===================================================================
                    # STEP 2: PARTIAL - Dimension A same, but B or C differs
                    # FORCE into 'Déjà vu' layer regardless of high score
                    # ===================================================================
                    if judgment == 'PARTIAL':
                        partial_count += 1
                        item['layer'] = 'Déjà vu'  # Force to lowest tier
                        item['intent_category'] = 'PARTIAL'
                        item['judgment_reason'] = reason
                        final_candidates.append(item)
                        print(f"   ⚠️ [{i}] PARTIAL -> Forced to Déjà vu (Score: {score:.3f})")
                        continue

                    # ===================================================================
                    # STEP 3: PERFECT - All 3 dimensions match
                    # Assign layer based on cosine similarity score
                    # ===================================================================
                    if judgment == 'PERFECT':
                        perfect_count += 1
                        item['intent_category'] = 'PERFECT'
                        item['judgment_reason'] = reason

                        # Layer assignment by score (standard PRD Pyramid)
                        if score > 0.85:
                            item['layer'] = 'Precision'
                            print(f"   ✅ [{i}] PERFECT + Score {score:.3f} -> Precision")
                        elif score > 0.75:
                            item['layer'] = 'Resonance'
                            print(f"   ✅ [{i}] PERFECT + Score {score:.3f} -> Resonance")
                        else:
                            item['layer'] = 'Déjà vu'
                            print(f"   ✅ [{i}] PERFECT + Score {score:.3f} -> Déjà vu")

                        final_candidates.append(item)

                except json.JSONDecodeError as je:
                    print(f"   ⚠️ [{i}] JSON parse error: {je} -> Treating as MISMATCH")
                    mismatch_count += 1
                except Exception as inner_e:
                    print(f"   ⚠️ [{i}] LLM call error: {inner_e} -> Treating as MISMATCH")
                    mismatch_count += 1

            print(f"\n📊 Semantic Gatekeeper Summary:")
            print(f"   Input: {len(candidate_items)} candidates")
            print(f"   Safety Net (score < 0.635): {discarded_low_score} discarded")
            print(f"   MISMATCH (Core Focus differs): {mismatch_count} discarded")
            print(f"   PARTIAL (forced to Déjà vu): {partial_count} kept")
            print(f"   PERFECT (layer by score): {perfect_count} kept")
            print(f"   Output: {len(final_candidates)} candidates")

            return final_candidates

        except Exception as e:
            print(f"❌ Semantic Gatekeeper Failed: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return candidate_items  # Fail open to avoid breaking app

    def get_stratified_matches(self, user_query, candidate_queries, candidate_ids, source_ids=None, exclude_source_id=None, match_batch_id=None, api_key=None):
        """
        "Context First" Two-Step Retrieval Logic.

        Core Philosophy: Trust the Metadata (ABC/Batch) first. Rely on Semantic Scores second.

        STEP 1 - VIP CHECK (Metadata Priority):
            IF source_id matches match_batch_id -> BYPASS all score filters, return immediately.
            Label based on score: Precision (>0.85), Resonance (0.75-0.85), Déjà vu (<0.75).

        STEP 2 - SEMANTIC FALLBACK (Strict Scoring for External Data):
            Only for items that FAILED the VIP check.
            Apply strict 3-layer semantic filter:
              - Layer 1 (Precision): score > 0.85
              - Layer 2 (Resonance): 0.75 < score <= 0.85
              - Layer 3 (Déjà vu):   0.635 < score <= 0.75
            Discard if score <= 0.635 (QNF - Query Not Found).

        Summary: Internal data (ABC met) is always shown. External data only shown if score > 0.635.

        Args:
            user_query (str): The user's input query
            candidate_queries (list): List of candidate query strings
            candidate_ids (list): List of corresponding IDs
            source_ids (list): Optional list of source_ids for batch matching
            exclude_source_id (str): Optional source_id to exclude (prevents self-referencing)
            match_batch_id (str): Batch_id for VIP check (internal data matching)
            api_key (str): Optional API key for DeepSeek Consistency Layer

        Returns:
            list: List of dicts {'index': i, 'id': id, 'score': s, 'layer': str, 'is_internal': bool}
        """
        try:
            if not candidate_queries:
                return []

            # PRE-FILTER: Exclude candidates from the current interaction (anti-echo-chamber)
            if exclude_source_id is not None and source_ids is not None:
                filtered_indices = [
                    i for i, sid in enumerate(source_ids)
                    if sid != exclude_source_id
                ]
                if not filtered_indices:
                    return []  # All candidates were from current interaction

                candidate_queries = [candidate_queries[i] for i in filtered_indices]
                candidate_ids = [candidate_ids[i] for i in filtered_indices]
                source_ids = [source_ids[i] for i in filtered_indices]

            # Encode inputs
            query_embedding = self.model.encode([user_query], convert_to_numpy=True)
            candidate_embeddings = self.model.encode(candidate_queries, convert_to_numpy=True)

            # Calculate similarities
            similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]

            # SOURCE-LEVEL DEDUPLICATION (One Decoy Per Original Query)
            # Group candidates by source_id and keep only the best match per source
            if source_ids is not None and len(source_ids) == len(candidate_queries):
                unique_candidates = {}  # Key: source_id, Value: best candidate info

                for idx, score in enumerate(similarities):
                    source_id = source_ids[idx]
                    dedup_key = source_id if source_id is not None else f"orphan_{candidate_ids[idx]}"

                    candidate_info = {
                        'index': idx,
                        'id': candidate_ids[idx],
                        'score': float(score),
                        'query': candidate_queries[idx],
                        'source_id': source_id
                    }

                    if dedup_key not in unique_candidates or score > unique_candidates[dedup_key]['score']:
                        unique_candidates[dedup_key] = candidate_info

                deduplicated_items = list(unique_candidates.values())
            else:
                deduplicated_items = [
                    {'index': idx, 'id': candidate_ids[idx], 'score': float(similarities[idx]), 'query': candidate_queries[idx], 'source_id': None}
                    for idx in range(len(candidate_queries))
                ]

            # --- APPLY DEEPSEEK DUAL-VALIDATION LAYER ---
            # When API key is provided, this filter:
            # 1. Discards MISMATCH candidates (qualitative check)
            # 2. Assigns 'layer' based on score thresholds (quantitative check)
            # 3. Discards candidates with score <= 0.635
            consistency_applied = False
            if api_key:
                deduplicated_items = self.apply_consistency_filter(user_query, deduplicated_items, api_key)
                consistency_applied = True

            # ===================================================================
            # "CONTEXT FIRST" TWO-STEP RETRIEVAL
            # ===================================================================

            internal_matches = []  # VIP matches (Step 1)
            external_matches = []  # Semantic fallback candidates (Step 2)

            for item in deduplicated_items:
                score = item['score']
                item_source_id = item.get('source_id')

                # ---------------------------------------------------------
                # STEP 1: VIP CHECK (Metadata Priority)
                # If ABC condition is met, BYPASS all score filters.
                # ---------------------------------------------------------
                if match_batch_id is not None and item_source_id == match_batch_id:
                    # INTERNAL MATCH: Bypass score filters, always include
                    item['is_internal'] = True
                    # Assign semantic label based on score (for display purposes)
                    # Only set layer if not already set by consistency filter
                    if 'layer' not in item:
                        if score > 0.85:
                            item['layer'] = 'Precision'
                        elif score > 0.75:
                            item['layer'] = 'Resonance'
                        else:
                            item['layer'] = 'Déjà vu'
                    internal_matches.append(item)
                else:
                    # No metadata match, proceed to Step 2
                    item['is_internal'] = False
                    external_matches.append(item)

            # ---------------------------------------------------------
            # STEP 2: SEMANTIC FALLBACK (Strict Scoring for External Data)
            # Only apply score filters to items that failed VIP check.
            # NOTE: If consistency filter was applied, items already have
            #       'layer' set and low-score items were already discarded.
            # ---------------------------------------------------------
            precision = []
            resonance = []
            dejavu = []

            for item in external_matches:
                score = item['score']

                # If consistency filter already assigned layer, use it directly
                if 'layer' in item:
                    layer = item['layer']
                    if layer == 'Precision':
                        precision.append(item)
                    elif layer == 'Resonance':
                        resonance.append(item)
                    elif layer == 'Déjà vu':
                        dejavu.append(item)
                    # Items with other layers or no valid layer are implicitly discarded
                else:
                    # No consistency filter applied, classify by score
                    # Layer 1 (Precision): score > 0.85
                    if score > 0.85:
                        item['layer'] = 'Precision'
                        precision.append(item)
                    # Layer 2 (Resonance): 0.75 < score <= 0.85
                    elif score > 0.75:
                        item['layer'] = 'Resonance'
                        resonance.append(item)
                    # Layer 3 (Déjà vu): 0.635 < score <= 0.75
                    elif score > 0.635:
                        item['layer'] = 'Déjà vu'
                        dejavu.append(item)
                    # else: score <= 0.635 -> QNF (Query Not Found), discard

            # Sort each bucket by score descending
            internal_matches.sort(key=lambda x: x['score'], reverse=True)
            precision.sort(key=lambda x: x['score'], reverse=True)
            resonance.sort(key=lambda x: x['score'], reverse=True)
            dejavu.sort(key=lambda x: x['score'], reverse=True)

            # ===================================================================
            # SAMPLING STRATEGY: Internal first, then External by tier
            # ===================================================================
            final_results = []
            seen_ids = set()
            seen_contents = set()

            def add_unique_items(bucket_items, limit):
                """Helper to add unique items from a bucket."""
                count = 0
                for item in bucket_items:
                    if count >= limit:
                        break
                    if item['id'] in seen_ids:
                        continue
                    if item['query'] in seen_contents:
                        continue
                    final_results.append(item)
                    seen_ids.add(item['id'])
                    seen_contents.add(item['query'])
                    count += 1

            # 1. INTERNAL MATCHES FIRST (VIP - no limit, they earned it)
            add_unique_items(internal_matches, len(internal_matches))

            # 2. Fill with external matches by tier (up to 10 total)
            remaining = 10 - len(final_results)
            if remaining > 0:
                # Precision tier (up to 5)
                add_unique_items(precision, min(5, remaining))
                remaining = 10 - len(final_results)

            if remaining > 0:
                # Resonance tier (up to 5)
                add_unique_items(resonance, min(5, remaining))
                remaining = 10 - len(final_results)

            if remaining > 0:
                # Déjà vu tier (fill remainder)
                add_unique_items(dejavu, remaining)

            return final_results

        except Exception as e:
            print(f"Error during stratified matching: {e}")
            return []


def find_best_match(user_query):
    """
    Convenience function to find the best match for a user query.
    Creates a new SemanticMatcher instance.
    
    Args:
        user_query (str): The user's input query
        
    Returns:
        tuple: (best_match_text, similarity_score) or (None, None)
    """
    try:
        matcher = SemanticMatcher()
        return matcher.find_best_match(user_query)
    except Exception as e:
        print(f"Error in find_best_match: {e}")
        return None, None


if __name__ == "__main__":
    # Test the semantic matcher
    print("\n=== Testing Semantic Matcher ===\n")
    
    test_queries = [
        "I work as a developer in Seattle and I'm exhausted",
        "My phone battery dies quickly",
        "No match for this query should exist here xyz123"
    ]
    
    matcher = SemanticMatcher()
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        match, score = matcher.find_best_match(query)
        if match:
            print(f"Match: {match}")
            print(f"Score: {score:.4f}")
        else:
            print("No match found (score below threshold)")
