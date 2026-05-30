import ast
import unittest
from pathlib import Path

from llm_response_utils import extract_json_payload, sanitize_llm_text


ROOT = Path(__file__).resolve().parent.parent


class TestPhase1Refactor(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_minimax_configuration_replaces_deepseek(self):
        files = [
            "fortress_models.py",
            "app.py",
            "layer0_router.py",
            "layer1_matching.py",
            "layer2_confuser.py",
            "layer3_consistency.py",
            "layer4_decoy_factory.py",
            "decoy_worker.py",
            "main.py",
            "locales/en.json",
            "locales/zh.json",
        ]

        combined = "\n".join(self.read(path) for path in files)

        self.assertIn("MINIMAX_API_KEY", combined)
        self.assertIn("m2.7", combined)
        self.assertNotIn("deepseek-chat", combined)
        self.assertNotIn("https://api.deepseek.com", combined)
        self.assertNotIn("DeepSeek", combined)

    def test_primary_chat_system_prompt_uses_fortress_ai_identity(self):
        app_content = self.read("app.py")

        self.assertIn("You are Fortress AI, a helpful AI assistant.", app_content)
        self.assertNotIn("You are MiniMax, a helpful AI assistant.", app_content)

    def test_minimax_uses_working_china_endpoint(self):
        from fortress_models import MINIMAX_BASE_URL

        self.assertEqual(MINIMAX_BASE_URL, "https://api.minimaxi.com/v1")

    def test_embedding_layer_uses_siliconflow_api_configuration(self):
        files = [
            "fortress_models.py",
            "embedding_api.py",
            "layer1_matching.py",
            "layer4_decoy_factory.py",
            "decoy_worker.py",
            "debug_bge.py",
            "requirements.txt",
        ]

        combined = "\n".join(self.read(path) for path in files)

        from fortress_models import EMBEDDING_API_BASE, EMBEDDING_MODEL_NAME

        self.assertEqual(EMBEDDING_API_BASE, "https://api.siliconflow.cn/v1")
        self.assertEqual(EMBEDDING_MODEL_NAME, "BAAI/bge-m3")
        self.assertNotIn("SentenceTransformer", combined)
        self.assertNotIn("sentence-transformers", combined)
        self.assertIn("EMBEDDING_API_KEY", combined)
        self.assertNotIn("BAAI/bge-small-en-v1.5", combined)

    def test_decoy_generation_cascade_configuration_exists(self):
        from fortress_models import (
            GEMMA_API_BASE,
            GEMMA_API_KEY,
            GEMMA_MODEL_NAME,
            QWEN_API_BASE,
            QWEN_API_KEY,
            QWEN_MODEL_NAME,
        )
        from layer4_decoy_factory import GEMMA_PROVIDER, QWEN_PROVIDER

        self.assertEqual(
            GEMMA_API_BASE,
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        self.assertIsInstance(GEMMA_API_KEY, str)
        self.assertTrue(GEMMA_API_KEY.strip())
        self.assertEqual(GEMMA_MODEL_NAME, "gemma-4-31b-it")
        self.assertEqual(QWEN_API_BASE, "https://api.siliconflow.cn/v1")
        self.assertIsInstance(QWEN_API_KEY, str)
        self.assertTrue(QWEN_API_KEY.strip())
        self.assertEqual(QWEN_MODEL_NAME, "Qwen/Qwen3.5-397B-A17B")
        self.assertEqual(GEMMA_PROVIDER.base_url, GEMMA_API_BASE)
        self.assertEqual(GEMMA_PROVIDER.model_name, GEMMA_MODEL_NAME)
        self.assertEqual(QWEN_PROVIDER.base_url, QWEN_API_BASE)
        self.assertEqual(QWEN_PROVIDER.model_name, QWEN_MODEL_NAME)

    def test_llm_response_utils_handle_thinking_wrappers(self):
        wrapped_json = """<think>
internal reasoning
</think>
{"query":"masked query","response":"masked response"}"""
        wrapped_text = """<think>
reasoning
</think>
Final answer."""

        parsed = extract_json_payload(wrapped_json)

        self.assertEqual(parsed["query"], "masked query")
        self.assertEqual(parsed["response"], "masked response")
        self.assertEqual(sanitize_llm_text(wrapped_text), "Final answer.")

    def test_email_relay_code_is_commented_out_with_phase1_todo(self):
        app_content = self.read("app.py")
        db_content = self.read("database_manager.py")

        self.assertIn("TODO (Phase 1): Disabled email UI for medical privacy compliance", app_content)
        self.assertIn("TODO (Phase 1): Disabled for medical privacy compliance", db_content)

        app_ast = ast.parse(app_content)
        db_ast = ast.parse(db_content)

        app_function_names = {
            node.name for node in ast.walk(app_ast) if isinstance(node, ast.FunctionDef)
        }
        db_function_names = {
            node.name for node in ast.walk(db_ast) if isinstance(node, ast.FunctionDef)
        }

        self.assertNotIn("send_peer_message", app_function_names)
        self.assertNotIn("render_email_composer", app_function_names)
        self.assertNotIn("get_decoy_owner_email", db_function_names)

        for node in ast.walk(app_ast):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "button":
                    for keyword in node.keywords:
                        if keyword.arg == "help" and isinstance(keyword.value, ast.Constant):
                            self.assertNotEqual(keyword.value.value, "Message them")
                if node.func.attr == "dialog":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        self.assertNotEqual(node.args[0].value, "Message Anonymous Peer")


if __name__ == "__main__":
    unittest.main()
