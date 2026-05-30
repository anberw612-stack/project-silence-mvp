"""
Layer 4: Decoy Factory (Asynchronous Data Poisoning)

This module generates "parallel universe" versions of conversations (decoys)
to populate the database. This allows the system to serve high-fidelity
decoys instead of real user data, providing a Zero Latency Honeypot defense.

Implementation: Cascading multi-model fallback
- Phase 1: Probe Gemma with 3 attempts, continue to 5 if any succeed
- Phase 2: Fall back to Qwen with the same 3+2 pattern if Gemma fully fails
- Phase 3: Rescue the best malformed attempt into a minimal decoy so the
  pipeline never crashes without producing anything
"""

import json
import re
import time
import uuid
from dataclasses import dataclass
from typing import List, Optional, Tuple

import database_manager as db
from layer3_consistency import check_and_fix_response
from fortress_models import (
    GEMMA_API_BASE,
    GEMMA_API_KEY,
    GEMMA_MODEL_NAME,
    MINIMAX_BASE_URL,
    MINIMAX_CHAT_MODEL,
    QWEN_API_BASE,
    QWEN_API_KEY,
    QWEN_MODEL_NAME,
    build_llm_client,
    build_provider_client,
)
from llm_response_utils import extract_json_payload, sanitize_llm_text

# System prompt for generating decoys - Deep Structural Obfuscation
DECOY_SYSTEM_PROMPT = """You are the 'Confuser' Privacy Module - an expert in deep semantic obfuscation.
Task: Generate a 'Synthetic Decoy' that preserves the CORE INTENT but is UNRECOGNIZABLE to the original author.

GOAL: If the original author sees the decoy, they should NOT recognize it as derived from their query.

PROTOCOL - EXECUTE ALL 6 MANDATORY TRANSFORMATIONS:

1. **DOMAIN HARD SWAP** (Critical):
   - Change the specific field/tool/condition to a PARALLEL but DIFFERENT domain.
   - Example: "临床医学+科研" → "药学+药物研发" (both medical, but different paths)
   - Example: "Python debugging" → "Go performance tuning" (both programming, different focus)

2. **ENTITY & METRIC SWAP**:
   - Change test types: "英语六级" → "雅思/托福/GRE"
   - Change institutions: "北京大学" → "复旦大学" or "某985高校"
   - Change metrics to equivalent but different scales: "412分" → "5.5分" (different test systems)

3. **NUMERIC SHIFT**:
   - Ages: +/- 2-5 years
   - Scores: Change to equivalent level in different system
   - Durations: "3年" → "2年半" or "几年"

4. **SEQUENCE RESTRUCTURING** (Critical for unrecognizability):
   - REORDER the information elements in the sentence.
   - Example: [Major] → [Goal] → [Weakness] becomes [Goal] → [Weakness] → [Major]
   - Example: "我是X专业，想做Y，但Z很差" → "想从事Y方向，虽然Z是短板，目前在学X"

5. **TONE & PERSPECTIVE SHIFT**:
   - Change emotional tone: Anxious → Analytical, Humble → Confident
   - Change perspective: First person → Third person description
   - Change question style: Direct → Rhetorical, Seeking advice → Seeking validation
   - Example: "我适合读博吗？" → "这种情况申请博士现实吗？"

6. **SYNTACTIC VARIATION**:
   - Change sentence connectors: "但是" → "不过/然而/虽然...但"
   - Split or merge clauses
   - Add or remove hedging language

QUALITY CHECK - The decoy should:
✅ Preserve the abstract problem structure (someone asking about academic/career fit)
✅ Be unrecognizable to the original author
✅ Sound like a DIFFERENT person with a SIMILAR dilemma
❌ NOT be a simple find-and-replace of entities

OUTPUT FORMAT (JSON ONLY):
{
  "rationale": "1) Domain: 临床医学→药学; 2) Metric: 六级→雅思; 3) Sequence: reversed major/goal order; 4) Tone: anxious→reflective",
  "query": "The deeply transformed query",
  "response": "The correspondingly transformed response"
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

PROBE_ATTEMPTS = 3
MAX_CASCADE_ATTEMPTS = 5
MAX_PROVIDER_RETRIES = 2
REQUIRED_DECOY_FIELDS = ("query", "response")
RESCUE_KEY_PATTERNS = (
    "query",
    "response",
    "rationale",
    "symptoms",
    "emotion",
    "decoy_story",
)
RETRYABLE_ERROR_MARKERS = (
    "error code: 500",
    "error code: 502",
    "error code: 503",
    "error code: 504",
    "50507",
    "timeout",
    "timed out",
    "temporarily unavailable",
    "connection error",
)

MISSION_CONTEXT = """
[MISSION OBJECTIVE]
Target Outcome: Produce valid decoy JSON that preserves the user's abstract dilemma while sounding like a different person.

CRITICAL REQUIREMENTS:
1. The original author must NOT recognize the decoy as derived from their query
2. Apply ALL 6 transformations, especially SEQUENCE RESTRUCTURING
3. Change the ORDER of information elements, not just the entities
4. Shift the tone and perspective to sound like a DIFFERENT person

ANTI-PATTERN (DO NOT DO THIS):
❌ "我是临床医学专业，GPA 2.9，想读博" → "我是口腔医学专业，GPA 3.0，想读博"
   (This is just entity replacement - too recognizable!)

CORRECT PATTERN:
✅ "我是临床医学专业，GPA 2.9，想读博" → "考虑读博深造，但绩点只有3.1左右，药学方向的研究生不知道有没有机会"
   (Reordered structure, changed perspective, different domain)
"""


@dataclass(frozen=True)
class ProviderConfig:
    label: str
    base_url: str
    api_key: str
    model_name: str


GEMMA_PROVIDER = ProviderConfig(
    label="Gemma 4",
    base_url=GEMMA_API_BASE,
    api_key=GEMMA_API_KEY,
    model_name=GEMMA_MODEL_NAME,
)

QWEN_PROVIDER = ProviderConfig(
    label="Qwen 3.5",
    base_url=QWEN_API_BASE,
    api_key=QWEN_API_KEY,
    model_name=QWEN_MODEL_NAME,
)


def build_decoy_user_content(original_query: str, original_response: str) -> str:
    return f"""{MISSION_CONTEXT}

Original Query: {original_query}
Original Response: {original_response}"""


def validate_decoy_payload(payload) -> bool:
    if not isinstance(payload, dict):
        return False

    return all(
        isinstance(payload.get(field), str) and payload.get(field).strip()
        for field in REQUIRED_DECOY_FIELDS
    )


def normalize_decoy_payload(payload: dict, provider_label: str) -> dict:
    return {
        "query": payload["query"].strip(),
        "response": payload["response"].strip(),
        "rationale": (payload.get("rationale") or f"Generated by {provider_label}").strip(),
        "provider": provider_label,
    }


def is_retryable_provider_error(exc: Exception) -> bool:
    error_text = str(exc).lower()
    return any(marker in error_text for marker in RETRYABLE_ERROR_MARKERS)


def decode_candidate_value(value: str) -> str:
    if not value:
        return value

    if any(token in value for token in ("\\u", "\\n", "\\t", "\\r", '\\"', "\\\\")):
        try:
            return value.encode("utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            return value

    return value


def score_failed_decoy(raw_text: str) -> int:
    cleaned = sanitize_llm_text(raw_text or "")
    key_hits = sum(
        1
        for key in RESCUE_KEY_PATTERNS
        if re.search(rf'["\']?{re.escape(key)}["\']?\s*[:=]', cleaned, re.IGNORECASE)
    )
    open_braces = cleaned.count("{")
    close_braces = cleaned.count("}")
    paired_braces = min(open_braces, close_braces)
    brace_penalty = abs(open_braces - close_braces)
    quote_pairs = cleaned.count('"') // 2
    return key_hits * 10 + paired_braces * 3 + quote_pairs - brace_penalty * 2 + (1 if cleaned.strip() else 0)


def extract_candidate_field(raw_text: str, field_names: List[str]) -> Optional[str]:
    if not raw_text:
        return None

    for field_name in field_names:
        patterns = [
            re.compile(
                rf'[`"\']?{re.escape(field_name)}[`"\']?\s*:\s*"(?P<value>(?:\\.|[^"])*)"',
                re.DOTALL,
            ),
            re.compile(
                rf"[`\"']?{re.escape(field_name)}[`\"']?\s*:\s*'(?P<value>(?:\\.|[^'])*)'",
                re.DOTALL,
            ),
            re.compile(
                rf'[`"\']?{re.escape(field_name)}[`"\']?\s*:\s*(?P<value>[^\n]+)',
                re.DOTALL,
            ),
        ]
        for pattern in patterns:
            match = pattern.search(raw_text)
            if match:
                value = match.group("value").strip().strip(",").strip()
                value = value.strip('`"\'')
                if value:
                    return decode_candidate_value(value)

    return None


def salvage_decoy_payload(raw_text: str, provider_label: str) -> Optional[dict]:
    if not raw_text:
        return None

    query = extract_candidate_field(raw_text, ["query", "decoy_query", "decoy_story", "story"])
    response = extract_candidate_field(raw_text, ["response", "answer", "advice"])
    rationale = extract_candidate_field(raw_text, ["rationale", "reason", "explanation"])

    if not query or not response:
        return None

    return normalize_decoy_payload(
        {
            "query": query,
            "response": response,
            "rationale": rationale or f"Recovered from malformed {provider_label} output.",
        },
        provider_label,
    )


def rescue_best_failed_decoy(
    failed_attempts: List[str],
    original_query: str,
    original_response: str,
) -> dict:
    if failed_attempts:
        best_raw = max(failed_attempts, key=score_failed_decoy)
    else:
        best_raw = ""

    cleaned = sanitize_llm_text(best_raw).replace("```json", "").replace("```", "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)

    rescued_query = (
        extract_candidate_field(best_raw, ["query", "decoy_story", "story"])
        or cleaned[:220].strip()
        or "匿名用户在健康变化、家庭计划和职业选择之间感到两难，想知道下一步该如何更稳妥地安排。"
    )
    rescued_response = (
        extract_candidate_field(best_raw, ["response", "advice", "emotion"])
        or (sanitize_llm_text(original_response or "").strip()[:240] if original_response else "")
        or "建议先把身体评估和时间线梳理清楚，再把家庭计划与工作节奏一起纳入决策，优先处理最影响安全和确定性的部分。"
    )
    rescued_rationale = (
        extract_candidate_field(best_raw, ["rationale", "symptoms", "emotion"])
        or "Rescue Mode fallback from malformed decoy output."
    )

    return {
        "query": rescued_query,
        "response": rescued_response,
        "rationale": rescued_rationale,
        "provider": "Rescue Mode",
        "raw_text": best_raw,
        "rescue_score": score_failed_decoy(best_raw),
    }


def attempt_decoy_generation(
    provider: ProviderConfig,
    user_content: str,
    attempts: int,
    client=None,
) -> Tuple[List[dict], List[str]]:
    if attempts <= 0:
        return [], []

    if client is None:
        client = build_provider_client(provider.api_key, provider.base_url)
    valid_decoys: List[dict] = []
    failed_attempts: List[str] = []

    for attempt_index in range(1, attempts + 1):
        print(f"   📡 {provider.label} attempt {attempt_index}/{attempts}", end="")

        raw_text = ""
        last_error = None
        attempt_succeeded = False

        for retry_index in range(MAX_PROVIDER_RETRIES + 1):
            try:
                response = client.chat.completions.create(
                    model=provider.model_name,
                    messages=[
                        {"role": "system", "content": DECOY_SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=1.0,
                    response_format={"type": "json_object"},
                    max_tokens=2000,
                )

                raw_text = response.choices[0].message.content or ""
                if not raw_text:
                    last_error = ValueError("Empty model output")
                    break

                try:
                    payload = extract_json_payload(raw_text)
                except Exception:
                    payload = salvage_decoy_payload(raw_text, provider.label)

                if validate_decoy_payload(payload):
                    decoy = normalize_decoy_payload(payload, provider.label)
                    valid_decoys.append(decoy)
                    attempt_succeeded = True
                    print(" ✅ Valid JSON")
                    break

                last_error = ValueError("Missing required fields")
                break

            except Exception as exc:
                last_error = exc
                if is_retryable_provider_error(exc) and retry_index < MAX_PROVIDER_RETRIES:
                    print(" ↻ Retry", end="")
                    time.sleep(1 + retry_index)
                    continue
                break
        else:
            last_error = ValueError("Unknown generation failure")

        if attempt_succeeded:
            continue

        failed_attempts.append(raw_text or str(last_error) if last_error else "")
        print(f" ⚠️ Failed: {last_error}")

    return valid_decoys, failed_attempts


def generate_decoy_candidates_with_cascade(
    original_query: str,
    original_response: str,
    max_decoys: int = MAX_CASCADE_ATTEMPTS,
) -> Tuple[List[dict], List[str]]:
    target_attempts = max(1, min(max_decoys, MAX_CASCADE_ATTEMPTS))
    probe_attempts = min(PROBE_ATTEMPTS, target_attempts)
    remaining_attempts = max(0, target_attempts - probe_attempts)
    user_content = build_decoy_user_content(original_query, original_response)
    failed_attempts: List[str] = []

    print("🔬 Starting cascading fallback decoy generation")
    print(f"   Target attempts: {target_attempts}")

    gemma_client = build_provider_client(GEMMA_PROVIDER.api_key, GEMMA_PROVIDER.base_url)
    gemma_valid, gemma_failed = attempt_decoy_generation(
        GEMMA_PROVIDER,
        user_content,
        probe_attempts,
        client=gemma_client,
    )
    failed_attempts.extend(gemma_failed)

    if gemma_valid:
        extra_valid, extra_failed = attempt_decoy_generation(
            GEMMA_PROVIDER,
            user_content,
            remaining_attempts,
            client=gemma_client,
        )
        failed_attempts.extend(extra_failed)
        valid_decoys = (gemma_valid + extra_valid)[:target_attempts]
        print(f"   ✅ Gemma succeeded during probe. Saving {len(valid_decoys)} usable decoys.")
        return valid_decoys, failed_attempts

    print("   ⚠️ Gemma probe fully failed. Falling back to Qwen.")
    qwen_client = build_provider_client(QWEN_PROVIDER.api_key, QWEN_PROVIDER.base_url)
    qwen_valid, qwen_failed = attempt_decoy_generation(
        QWEN_PROVIDER,
        user_content,
        probe_attempts,
        client=qwen_client,
    )
    failed_attempts.extend(qwen_failed)

    if qwen_valid:
        extra_valid, extra_failed = attempt_decoy_generation(
            QWEN_PROVIDER,
            user_content,
            remaining_attempts,
            client=qwen_client,
        )
        failed_attempts.extend(extra_failed)
        valid_decoys = (qwen_valid + extra_valid)[:target_attempts]
        print(f"   ✅ Qwen rescued generation. Saving {len(valid_decoys)} usable decoys.")
        return valid_decoys, failed_attempts

    print("   ⚠️ Qwen probe fully failed. Entering Rescue Mode.")
    rescued_decoy = rescue_best_failed_decoy(failed_attempts, original_query, original_response)
    return [rescued_decoy], failed_attempts


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


def call_judge(original_query, decoy_query, api_key, base_url=MINIMAX_BASE_URL):
    """
    Call the Judge LLM to determine if a decoy matches the original's core intent.
    
    Args:
        original_query (str): The original user query
        decoy_query (str): The generated decoy query
        api_key (str): MiniMax API key
        base_url (str): API base URL
        
    Returns:
        str: "MATCH" or "MISMATCH"
    """
    try:
        client = build_llm_client(api_key=api_key, base_url=base_url)
        
        user_content = f"""ORIGINAL QUERY: {original_query}

DECOY QUERY: {decoy_query}

Compare these two queries. Do they share the same Core Intent (A), Focus (B), and Abstract Need (C)?"""

        response = client.chat.completions.create(
            model=MINIMAX_CHAT_MODEL,
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
            
        result = extract_json_payload(content)
        verdict = result.get('verdict', 'MISMATCH').upper()
        reason = result.get('reason', 'No reason provided')
        
        print(f"      📋 Judge Reason: {reason[:60]}...")
        
        return verdict if verdict in ["MATCH", "MISMATCH"] else "MISMATCH"
        
    except Exception as e:
        print(f"      ⚠️ Judge Error: {e}")
        return "MISMATCH"


def generate_decoys(original_query, original_response, api_key, num_decoys=5, base_url=MINIMAX_BASE_URL, source_id=None, owner_user_id=None):
    """
    Generate decoy conversations using cascading multi-model fallback.

    Args:
        original_query (str): The original user query
        original_response (str): The original AI response
        api_key (str): MiniMax API key, still used for Layer 3 response cleanup
        num_decoys (int): Maximum number of usable decoys to keep (capped at 5)
        base_url (str): Unused in cascade mode, kept for compatibility
        source_id (str): Optional source_id to tag decoys for deduplication
        owner_user_id (str): The user_id of the decoy creator
    """
    try:
        if not original_query:
            return

        batch_id = source_id if source_id else str(uuid.uuid4())
        target_decoys = max(1, min(num_decoys, MAX_CASCADE_ATTEMPTS))
        print(f"   Batch ID: {batch_id[:8]}...")

        valid_decoys, failed_attempts = generate_decoy_candidates_with_cascade(
            original_query=original_query,
            original_response=original_response,
            max_decoys=target_decoys,
        )

        if not valid_decoys:
            print("⚠️ Cascading fallback produced no usable decoys.")
            return

        print(f"\n{'='*60}")
        print("🏁 Cascading Decoy Generation Complete")
        print(f"   Valid Decoys: {len(valid_decoys)}/{target_decoys}")
        print(f"   Failed Attempts Captured: {len(failed_attempts)}")
        print(f"{'='*60}")

        for i, d in enumerate(valid_decoys):
            try:
                rationale_preview = d.get('rationale', 'N/A')[:50]
                provider_label = d.get('provider', 'Unknown Provider')
                print(f"   Saving [{i+1}] from {provider_label}: {rationale_preview}...")

                # Fix response (Layer 3 consistency)
                print(f"   [L4] Fixing response via Layer 3...")
                fixed_response = check_and_fix_response(d['response'], api_key) if api_key else d['response']
                print(f"   [L4] Response fixed, length: {len(fixed_response)}")

                # Extract topics from rationale for categorization
                topics = extract_topics_from_rationale(d.get('rationale', ''))
                print(f"   [L4] Extracted topics: {topics}")

                # Save to GLOBAL DECOYS table (shared across all users)
                # owner_user_id is stored for email relay but NOT exposed in UI
                print(f"   [L4] Calling db.save_global_decoy() -> global_decoys table")
                print(f"   [L4] Query: {d['query'][:60]}...")
                print(f"   [L4] Source ID: {batch_id[:8]}...")
                print(f"   [L4] Owner User ID: {owner_user_id[:8] if owner_user_id else 'None'}...")

                result_id = db.save_global_decoy(
                    query=d['query'],
                    response=fixed_response,
                    topics=topics,
                    source_id=batch_id,
                    owner_user_id=owner_user_id
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
