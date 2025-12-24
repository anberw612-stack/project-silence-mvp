from layer1_matching import SemanticMatcher, MOCK_DB
from sklearn.metrics.pairwise import cosine_similarity

# Initialize matcher with BAAI/bge-small-zh-v1.5
# (Default params updated in layer1_matching.py)
matcher = SemanticMatcher(threshold=0.0)

print("\n=== Debugging BAAI/bge Scores ===")

# Special Test for User's "Surprise" Scenario
# "Movie" vs "Novel" (Déjà vu concept)
query_concept = "Movie about a man who realizes he is a character in a novel"
target_concept = "A novel where the protagonist discovers he is in a movie" 

# Manual embeddings for the concept test
emb1 = matcher.model.encode([query_concept], convert_to_numpy=True)
emb2 = matcher.model.encode([target_concept], convert_to_numpy=True)
concept_score = cosine_similarity(emb1, emb2)[0][0]

print(f"\nConcept Test: 'Movie' vs 'Novel' (Déjà vu)")
print(f"  Score: {concept_score:.4f}")
if 0.45 <= concept_score <= 0.70:
    print("  REL RESULT: ✅ In Discovery/Surprise Range (0.45-0.70)")
else:
    print(f"  REL RESULT: ⚠️  Unexpected Range (Thresholds: {matcher.threshold})")

# Standard Tests against MOCK_DB
test_queries = [
    ("How do I cook spaghetti carbonara?", "Should match 'authentic carbonara' (> 0.60)"),
    ("我的老板太苛刻了", "Should match 'I hate my boss' (> 0.60)"),
    ("PhD in Pharmacy", "Should be NOISE (< 0.45)")
]

for query, desc in test_queries:
    print(f"\nQuery: {query}")
    print(f"Goal: {desc}")
    
    db_embeddings = matcher.db_embeddings
    query_embedding = matcher.model.encode([query], convert_to_numpy=True)
    
    similarities = cosine_similarity(query_embedding, db_embeddings)[0]
    
    # Print top 3 matches
    indices = similarities.argsort()[::-1][:3]
    for idx in indices:
        score = similarities[idx]
        star = "★" if score > 0.45 else " " 
        print(f"  {star} Score: {score:.4f} - {MOCK_DB[idx]}")
