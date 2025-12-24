import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import layer1_matching

class TestConsistencyLayer(unittest.TestCase):
    @patch('layer1_matching.OpenAI')
    @patch('layer1_matching.SentenceTransformer')
    def test_apply_consistency_filter(self, mock_st_class, mock_openai_class):
        # Setup mocks
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock model load so SemanticMatcher inits
        mock_st = MagicMock()
        mock_st_class.return_value = mock_st
        mock_st.encode.return_value = [[0.1, 0.2]] # minimal embedding
        
        matcher = layer1_matching.SemanticMatcher()
        
        # Test Data
        candidates = [
            {'query': "Candidate 0 (Valid)", 'id': 0, 'score': 0.8},
            {'query': "Candidate 1 (Invalid - Wrong Intent)", 'id': 1, 'score': 0.8},
            {'query': "Candidate 2 (Valid)", 'id': 2, 'score': 0.8}
        ]
        
        # Scenario 1: API returns indices [0, 2]
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({"valid_indices": [0, 2]})))]
        mock_client.chat.completions.create.return_value = mock_response
        
        filtered = matcher.apply_consistency_filter("User Query", candidates, api_key="test-key")
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['id'], 0)
        self.assertEqual(filtered[1]['id'], 2)
        print("Test 1: Filter Logic Passed (Kept 0 & 2)")
        
        # Scenario 2: No API Key (Should skip filter)
        filtered_no_key = matcher.apply_consistency_filter("User Query", candidates, api_key=None)
        self.assertEqual(len(filtered_no_key), 3)
        print("Test 2: Skip Logic Passed")
        
        # Scenario 3: API Exception (Fail Open)
        mock_client.chat.completions.create.side_effect = Exception("API Down")
        filtered_fail_open = matcher.apply_consistency_filter("User Query", candidates, api_key="test-key")
        self.assertEqual(len(filtered_fail_open), 3)
        print("Test 3: Fail-Open Logic Passed")

if __name__ == '__main__':
    unittest.main()
