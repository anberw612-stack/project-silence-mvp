import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add parent directory to path to import layer4
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import layer4_decoy_factory

class TestDecoyFactory(unittest.TestCase):
    @patch('layer4_decoy_factory.OpenAI')
    @patch('layer4_decoy_factory.SentenceTransformer')
    @patch('layer4_decoy_factory.cosine_similarity')
    @patch('layer4_decoy_factory.db')
    @patch('layer4_decoy_factory.check_and_fix_response')
    def test_strict_bounds_and_batch_logic(self, mock_fix, mock_db, mock_similarity, mock_st_class, mock_openai_class):
        # Setup mocks
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_model = MagicMock()
        mock_st_class.return_value = mock_model
        # Mock encoding to just return random distinct vectors so they aren't identical
        mock_model.encode.return_value = [[1.0, 0.0]] 

        # We will simulate 4 API calls with specific similarity scores
        # Call 1: 0.95 (Too similar - REJECT)
        # Call 2: 0.60 (Too different - REJECT)
        # Call 3: 0.80 (Valid - SAVE)
        # Call 4: 0.75 (Valid - SAVE)
        # -> Loop should exit because we hit 2 valid decoys
        
        # Mock cosine_similarity returns. It returns a 2D array [[score]]
        mock_similarity.side_effect = [
            [[0.95]], # Call 1
            [[0.60]], # Call 2
            [[0.80]], # Call 3
            [[0.75]], # Call 4
        ]
        
        # Mock API responses
        def side_effect_completions(*args, **kwargs):
            return MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({
                "query": "mock query",
                "response": "mock response"
            })))])
            
        mock_client.chat.completions.create.side_effect = side_effect_completions
        
        mock_fix.return_value = "fixed response"

        # Run the function
        layer4_decoy_factory.generate_decoys(
            original_query="test query", 
            original_response="test response", 
            api_key="fake-key",
            num_decoys=3 # Should be ignored
        )

        # Verification
        
        # 1. API Calls: Should be exactly 4
        self.assertEqual(mock_client.chat.completions.create.call_count, 4)
        
        # 2. Database Saves: Should be exactly 2 (Calls 3 and 4)
        self.assertEqual(mock_db.save_conversation.call_count, 2)
        
        # 3. Verify similarity checks were done 4 times
        self.assertEqual(mock_similarity.call_count, 4)

        print("Test passed: 4 calls made, 2 saved, strictly adhering to bounds.")

    @patch('layer4_decoy_factory.OpenAI')
    @patch('layer4_decoy_factory.SentenceTransformer')
    @patch('layer4_decoy_factory.cosine_similarity')
    @patch('layer4_decoy_factory.db')
    @patch('layer4_decoy_factory.check_and_fix_response')
    def test_max_call_limit(self, mock_fix, mock_db, mock_similarity, mock_st_class, mock_openai_class):
        # Setup mocks
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_model = MagicMock()
        mock_st_class.return_value = mock_model
        
        # All calls return invalid score 0.90
        mock_similarity.return_value = [[0.90]]
        
        def side_effect_completions(*args, **kwargs):
            return MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({
                "query": "mock query",
                "response": "mock response"
            })))])
        mock_client.chat.completions.create.side_effect = side_effect_completions
        
        # Run function
        layer4_decoy_factory.generate_decoys(
            original_query="test query", 
            original_response="test response", 
            api_key="fake-key"
        )
        
        # Should hit 15 calls and stop, saving 0
        self.assertEqual(mock_client.chat.completions.create.call_count, 15)
        self.assertEqual(mock_db.save_conversation.call_count, 0)
        print("Test passed: Hit 15 call limit with 0 saved.")

if __name__ == '__main__':
    unittest.main()
