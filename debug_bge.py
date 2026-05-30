from layer1_matching import SemanticMatcher, MOCK_DB
from embedding_api import cosine_similarity_score, cosine_similarity_scores, get_embedding_vectors

matcher = SemanticMatcher(threshold=0.0)

print("\n=== Debugging Remote Embedding Scores ===")

# Special Test for User's "Surprise" Scenario
# "Movie" vs "Novel" (Déjà vu concept)
query_concept = "Movie about a man who realizes he is a character in a novel"
target_concept = "A novel where the protagonist discovers he is in a movie" 

concept_embeddings = get_embedding_vectors([query_concept, target_concept])
concept_score = cosine_similarity_score(concept_embeddings[0], concept_embeddings[1])

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
    
    embeddings = get_embedding_vectors([query, *MOCK_DB])
    query_embedding = embeddings[0]
    db_embeddings = embeddings[1:]
    similarities = cosine_similarity_scores(query_embedding, db_embeddings)
    
    # Print top 3 matches
    indices = similarities.argsort()[::-1][:3]
    for idx in indices:
        score = similarities[idx]
        star = "★" if score > 0.45 else " " 
        print(f"  {star} Score: {score:.4f} - {MOCK_DB[idx]}")
