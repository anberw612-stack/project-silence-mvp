import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add parent directory to path to import layer4
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import layer4_decoy_factory

class TestDecoyFactory(unittest.TestCase):
    def _mock_response(self, payload):
        return MagicMock(choices=[MagicMock(message=MagicMock(content=payload))])

    def test_attempt_decoy_generation_salvages_json_like_response(self):
        client = MagicMock()
        client.chat.completions.create.return_value = self._mock_response(
            """<thought>internal reasoning</thought>{
  'rationale': 'changed domain',
  'query': '关于目前的优先级排序我比较迷茫',
  'response': '建议先通过专业医疗评估',
}"""
        )

        valid_decoys, failed_attempts = layer4_decoy_factory.attempt_decoy_generation(
            layer4_decoy_factory.GEMMA_PROVIDER,
            "test user content",
            attempts=1,
            client=client,
        )

        self.assertEqual(len(valid_decoys), 1)
        self.assertEqual(valid_decoys[0]["query"], "关于目前的优先级排序我比较迷茫")
        self.assertEqual(valid_decoys[0]["response"], "建议先通过专业医疗评估")
        self.assertEqual(failed_attempts, [])

    def test_attempt_decoy_generation_salvages_bullet_style_fields(self):
        client = MagicMock()
        client.chat.completions.create.return_value = self._mock_response(
            """<thought>reasoning</thought>
*   `rationale`: "1) Domain swapped"
*   `query`: "关于目前的优先级排序我比较迷茫"
*   `response`: "建议先通过专业医疗评估"
"""
        )

        valid_decoys, failed_attempts = layer4_decoy_factory.attempt_decoy_generation(
            layer4_decoy_factory.GEMMA_PROVIDER,
            "test user content",
            attempts=1,
            client=client,
        )

        self.assertEqual(len(valid_decoys), 1)
        self.assertEqual(valid_decoys[0]["query"], "关于目前的优先级排序我比较迷茫")
        self.assertEqual(valid_decoys[0]["response"], "建议先通过专业医疗评估")
        self.assertEqual(failed_attempts, [])

    def test_attempt_decoy_generation_retries_transient_provider_errors(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            Exception("Error code: 500 - provider unstable"),
            Exception("Error code: 500 - provider unstable"),
            self._mock_response(json.dumps({
                "query": "retry decoy query",
                "response": "retry decoy response",
                "rationale": "recovered after retries"
            })),
        ]

        valid_decoys, failed_attempts = layer4_decoy_factory.attempt_decoy_generation(
            layer4_decoy_factory.QWEN_PROVIDER,
            "test user content",
            attempts=1,
            client=client,
        )

        self.assertEqual(client.chat.completions.create.call_count, 3)
        self.assertEqual(len(valid_decoys), 1)
        self.assertEqual(valid_decoys[0]["query"], "retry decoy query")
        self.assertEqual(failed_attempts, [])

    @patch('layer4_decoy_factory.build_provider_client')
    @patch('layer4_decoy_factory.db.save_global_decoy')
    @patch('layer4_decoy_factory.check_and_fix_response')
    def test_generate_decoys_uses_gemma_for_all_five_attempts_when_probe_succeeds(self, mock_fix, mock_save_global_decoy, mock_build_provider_client):
        gemma_client = MagicMock()
        qwen_client = MagicMock()
        mock_build_provider_client.side_effect = [gemma_client, qwen_client]
        mock_fix.return_value = "fixed response"
        mock_save_global_decoy.side_effect = ["id-1", "id-2", "id-3", "id-4", "id-5"]

        gemma_client.chat.completions.create.side_effect = [
            self._mock_response(json.dumps({
                "query": "decoy query 1",
                "response": "decoy response 1",
                "rationale": "changed framing"
            })),
            self._mock_response(json.dumps({
                "query": "decoy query 2",
                "response": "decoy response 2",
                "rationale": "changed domain"
            })),
            self._mock_response("not json at all"),
            self._mock_response(json.dumps({
                "query": "decoy query 3",
                "response": "decoy response 3",
                "rationale": "changed tone"
            })),
            self._mock_response(json.dumps({
                "query": "decoy query 4",
                "response": "decoy response 4",
                "rationale": "changed structure"
            })),
        ]

        layer4_decoy_factory.generate_decoys(
            original_query="test query",
            original_response="test response",
            api_key="fake-key",
            num_decoys=5
        )

        self.assertEqual(gemma_client.chat.completions.create.call_count, 5)
        self.assertEqual(qwen_client.chat.completions.create.call_count, 0)
        self.assertEqual(mock_save_global_decoy.call_count, 4)
        mock_build_provider_client.assert_any_call(
            layer4_decoy_factory.GEMMA_PROVIDER.api_key,
            layer4_decoy_factory.GEMMA_PROVIDER.base_url,
        )

    @patch('layer4_decoy_factory.build_provider_client')
    @patch('layer4_decoy_factory.db.save_global_decoy')
    @patch('layer4_decoy_factory.check_and_fix_response')
    def test_generate_decoys_falls_back_to_qwen_after_three_gemma_failures(self, mock_fix, mock_save_global_decoy, mock_build_provider_client):
        gemma_client = MagicMock()
        qwen_client = MagicMock()
        mock_build_provider_client.side_effect = [gemma_client, qwen_client]
        mock_fix.return_value = "fixed response"
        mock_save_global_decoy.side_effect = ["id-1", "id-2"]

        gemma_client.chat.completions.create.side_effect = [
            self._mock_response("gemma failure 1"),
            self._mock_response("gemma failure 2"),
            self._mock_response("gemma failure 3"),
        ]
        qwen_client.chat.completions.create.side_effect = [
            self._mock_response(json.dumps({
                "query": "qwen decoy 1",
                "response": "qwen response 1",
                "rationale": "rescued by qwen"
            })),
            self._mock_response("qwen malformed"),
            self._mock_response(json.dumps({
                "query": "qwen decoy 2",
                "response": "qwen response 2",
                "rationale": "rescued by qwen again"
            })),
            self._mock_response("qwen malformed 2"),
            self._mock_response("qwen malformed 3"),
        ]

        layer4_decoy_factory.generate_decoys(
            original_query="test query",
            original_response="test response",
            api_key="fake-key",
            num_decoys=5
        )

        self.assertEqual(gemma_client.chat.completions.create.call_count, 3)
        self.assertEqual(qwen_client.chat.completions.create.call_count, 5)
        self.assertEqual(mock_save_global_decoy.call_count, 2)
        self.assertEqual(
            mock_build_provider_client.call_args_list[0].args,
            (
                layer4_decoy_factory.GEMMA_PROVIDER.api_key,
                layer4_decoy_factory.GEMMA_PROVIDER.base_url,
            ),
        )
        self.assertEqual(
            mock_build_provider_client.call_args_list[1].args,
            (
                layer4_decoy_factory.QWEN_PROVIDER.api_key,
                layer4_decoy_factory.QWEN_PROVIDER.base_url,
            ),
        )

    def test_rescue_mode_selects_best_failed_sample(self):
        failed_attempts = [
            "plain text with nothing useful",
            '{"query":"rescued query","response":"rescued response"',
            '{"symptoms":"fatigue","emotion":"anxious","decoy_story":"shifted career context"}',
        ]

        rescued = layer4_decoy_factory.rescue_best_failed_decoy(
            failed_attempts=failed_attempts,
            original_query="original query",
            original_response="original response",
        )

        self.assertIsNotNone(rescued)
        self.assertIn("query", rescued)
        self.assertIn("response", rescued)
        self.assertTrue(rescued["query"])
        self.assertTrue(rescued["response"])

    def test_rescue_mode_preserves_utf8_text(self):
        failed_attempts = [
            '{"query":"关于目前的优先级排序我比较迷茫","response":"建议先通过专业医疗评估","rationale":"测试"}'
        ]

        rescued = layer4_decoy_factory.rescue_best_failed_decoy(
            failed_attempts=failed_attempts,
            original_query="original query",
            original_response="original response",
        )

        self.assertEqual(rescued["query"], "关于目前的优先级排序我比较迷茫")
        self.assertEqual(rescued["response"], "建议先通过专业医疗评估")
        self.assertEqual(rescued["rationale"], "测试")

if __name__ == '__main__':
    unittest.main()
