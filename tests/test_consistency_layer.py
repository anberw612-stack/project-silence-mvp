import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import layer1_matching

class TestConsistencyLayer(unittest.TestCase):
    @patch('layer1_matching.rerank_documents')
    def test_apply_consistency_filter(self, mock_rerank_documents):
        matcher = layer1_matching.SemanticMatcher()

        candidates = [
            {'query': "Candidate 0 (Valid)", 'id': 0, 'score': 0.8},
            {'query': "Candidate 1 (Invalid - Wrong Intent)", 'id': 1, 'score': 0.8},
            {'query': "Candidate 2 (Valid)", 'id': 2, 'score': 0.8}
        ]

        mock_rerank_documents.return_value = [
            {"index": 0, "relevance_score": 0.81},
            {"index": 1, "relevance_score": 0.18},
            {"index": 2, "relevance_score": 0.47},
        ]

        filtered = matcher.apply_consistency_filter("User Query", candidates)

        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['id'], 0)
        self.assertEqual(filtered[0]['layer'], 'Resonance')
        self.assertEqual(filtered[1]['id'], 2)
        self.assertEqual(filtered[1]['layer'], 'Déjà vu')
        self.assertAlmostEqual(filtered[0]['gatekeeper_score'], 0.81)
        self.assertAlmostEqual(filtered[1]['gatekeeper_score'], 0.47)

        filtered_no_key = matcher.apply_consistency_filter("User Query", candidates, gatekeeper_enabled=False)
        self.assertEqual(len(filtered_no_key), 3)

        mock_rerank_documents.side_effect = Exception("API Down")
        filtered_fail_open = matcher.apply_consistency_filter("User Query", candidates)
        self.assertEqual(len(filtered_fail_open), 3)

    @patch('layer1_matching.rerank_documents')
    def test_apply_consistency_filter_uses_gatekeeper_score_ranges(self, mock_rerank_documents):
        matcher = layer1_matching.SemanticMatcher()
        candidates = [
            {'query': "Candidate 0 (Valid)", 'id': 0, 'score': 0.9},
            {'query': "Candidate 1 (Loose)", 'id': 1, 'score': 0.9},
            {'query': "Candidate 2 (Reject)", 'id': 2, 'score': 0.9},
        ]

        mock_rerank_documents.return_value = [
            {"index": 0, "relevance_score": 0.82},
            {"index": 1, "relevance_score": 0.44},
            {"index": 2, "relevance_score": 0.20},
        ]

        filtered = matcher.apply_consistency_filter("User Query", candidates)

        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['intent_category'], 'PERFECT')
        self.assertEqual(filtered[0]['layer'], 'Precision')
        self.assertEqual(filtered[1]['intent_category'], 'PARTIAL')
        self.assertEqual(filtered[1]['layer'], 'Déjà vu')

    @patch('layer1_matching.rerank_documents')
    @patch('layer1_matching.get_embedding_vectors')
    def test_get_stratified_matches_uses_api_vectors(self, mock_get_embedding_vectors, mock_rerank_documents):
        matcher = layer1_matching.SemanticMatcher(threshold=0.0)

        mock_get_embedding_vectors.side_effect = [
            [
                [1.0, 0.0],
                [0.9, 0.1],
                [0.1, 0.9],
            ],
        ]
        mock_rerank_documents.return_value = [
            {"index": 0, "relevance_score": 0.9},
            {"index": 1, "relevance_score": 0.1},
        ]

        results = matcher.get_stratified_matches(
            user_query="I have a private medical concern",
            candidate_queries=["similar medical concern", "unrelated topic"],
            candidate_ids=["a", "b"],
            gatekeeper_enabled=True,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "a")
        self.assertEqual(results[0]["layer"], "Precision")
        self.assertAlmostEqual(results[0]["gatekeeper_score"], 0.9)

    def test_app_enables_gatekeeper_on_main_match_path(self):
        app_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app.py",
        )
        with open(app_path, "r", encoding="utf-8") as handle:
            app_source = handle.read()

        self.assertIn("gatekeeper_enabled=True", app_source)

if __name__ == '__main__':
    unittest.main()
