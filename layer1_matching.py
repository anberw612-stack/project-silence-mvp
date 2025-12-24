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



class SemanticMatcher:
    """
    Semantic matching engine that uses sentence transformers to find
    the most similar query from a predefined database.
    """
    
    def __init__(self, model_name='BAAI/bge-small-zh-v1.5', threshold=GLOBAL_MIN_THRESHOLD):
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
        Dual-Validation & Classification System.

        Step 1 (Qualitative): LLM classifies candidates as PERFECT/PARTIAL/MISMATCH.
                              MISMATCH candidates are immediately discarded.

        Step 2 (Quantitative): For PERFECT/PARTIAL candidates, apply semantic thresholds
                               to determine their Layer (Precision/Resonance/Déjà vu).
                               Candidates with score <= 0.635 are discarded (even if PERFECT intent).

        Args:
            user_query (str): The original user query.
            candidate_items (list): List of candidate dicts with 'query', 'id', 'score', etc.
            api_key (str): DeepSeek API key.

        Returns:
            list: Filtered list of candidate_items with 'layer' key populated.
        """
        if not api_key:
            print("⚠️ No API key provided for Consistency Layer. Skipping filter.")
            return candidate_items

        if not candidate_items:
            return []

        print(f"🧠 Dual-Validation Filter: Processing {len(candidate_items)} candidates...")

        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

            candidates_text = "\n".join([f"[{i}] {item['query']}" for i, item in enumerate(candidate_items)])

            prompt = f"""
Analyze the User Query based on 3 dimensions:
A. **Core Focus** (e.g., Academic Stress, Career Planning, Romance)
B. **Emotional Intent** (e.g., Seeking Comfort, Seeking Information, Venting, Boasting)
C. **Core Need** (e.g., "I need empathy", "I need a tutorial", "I need validation")

User Query: "{user_query}"

Classify each candidate in the list below into one of three categories:
- **PERFECT**: Matches Focus (A), Intent (B), AND Need (C) closely.
- **PARTIAL**: Matches Intent (B) OR Need (C), but not both perfectly.
- **MISMATCH**: Does not match Intent (B) or Need (C) at all.

Candidate List:
{candidates_text}

Return a JSON object mapping each candidate index to its category.
Example: {{ "0": "PERFECT", "1": "MISMATCH", "2": "PARTIAL", "3": "PERFECT" }}
"""
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            result = json.loads(response.choices[0].message.content)

            # ===================================================================
            # STEP 1: LLM Classification (Qualitative Check)
            # Discard MISMATCH candidates immediately.
            # ===================================================================
            qualified_candidates = []
            mismatch_count = 0

            for i, item in enumerate(candidate_items):
                category = result.get(str(i), "MISMATCH").upper()

                if category == "MISMATCH":
                    mismatch_count += 1
                    print(f"   ❌ [{i}] MISMATCH (Intent/Need mismatch) -> Discarded")
                else:
                    item['intent_category'] = category  # PERFECT or PARTIAL
                    qualified_candidates.append(item)

            print(f"   Step 1 Result: {mismatch_count} MISMATCH discarded, {len(qualified_candidates)} remain")

            # ===================================================================
            # STEP 2: Semantic Classification (Quantitative Check)
            # Apply PRD Pyramid thresholds to determine Layer.
            # ===================================================================
            final_candidates = []

            for item in qualified_candidates:
                score = item.get('score', 0)
                intent = item.get('intent_category', 'PARTIAL')

                # Layer 1 (Precision): score > 0.85
                if score > 0.85:
                    item['layer'] = 'Precision'
                    final_candidates.append(item)
                    print(f"   ✅ [{item.get('id')}] {intent} + Score {score:.3f} -> Precision")

                # Layer 2 (Resonance): 0.75 < score <= 0.85
                elif score > 0.75:
                    item['layer'] = 'Resonance'
                    final_candidates.append(item)
                    print(f"   ✅ [{item.get('id')}] {intent} + Score {score:.3f} -> Resonance")

                # Layer 3 (Déjà vu): 0.635 < score <= 0.75
                elif score > 0.635:
                    item['layer'] = 'Déjà vu'
                    final_candidates.append(item)
                    print(f"   ✅ [{item.get('id')}] {intent} + Score {score:.3f} -> Déjà vu")

                # Kill Zone: score <= 0.635
                else:
                    print(f"   ❌ [{item.get('id')}] {intent} Intent but Low Score ({score:.3f}) -> Discarded")

            print(f"✅ Dual-Validation Complete: {len(candidate_items)} -> {len(final_candidates)} candidates")
            return final_candidates

        except Exception as e:
            print(f"❌ Dual-Validation Filter Failed: {e}")
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
