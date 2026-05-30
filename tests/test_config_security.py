import importlib
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestConfigSecurity(unittest.TestCase):
    def test_source_files_do_not_contain_live_secret_prefixes(self):
        checked_files = [
            ROOT / "fortress_models.py",
            ROOT / "README.md",
            ROOT / "app.py",
            ROOT / "layer4_decoy_factory.py",
            ROOT / "decoy_worker.py",
            ROOT / "embedding_api.py",
            ROOT / "rerank_api.py",
        ]

        combined = "\n".join(path.read_text(encoding="utf-8") for path in checked_files)

        self.assertNotIn("sk-", combined)
        self.assertNotIn("AI" + "za", combined)
        self.assertNotIn("ghp" + "_", combined)

    def test_readme_describes_current_fortress_stack(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Fortress", readme)
        self.assertIn("Qwen/Qwen3-Reranker-8B", readme)
        self.assertIn("BAAI/bge-m3", readme)
        self.assertNotIn("DeepSeek", readme)
        self.assertNotIn("sentence-transformers", readme)
        self.assertNotIn("all-MiniLM-L6-v2", readme)

    def test_runtime_avoids_local_numeric_model_dependencies(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        checked_files = [
            ROOT / "app.py",
            ROOT / "embedding_api.py",
            ROOT / "fortress_models.py",
            ROOT / "layer1_matching.py",
        ]
        combined_source = "\n".join(path.read_text(encoding="utf-8") for path in checked_files)
        database_source = (ROOT / "database_manager.py").read_text(encoding="utf-8")

        self.assertNotIn("numpy", requirements.lower())
        self.assertNotIn("import numpy", combined_source)
        self.assertNotIn("from numpy", combined_source)
        self.assertNotIn("from openai import OpenAI", combined_source)
        self.assertNotIn("from supabase import create_client", database_source)
        self.assertNotIn("import streamlit as st\n", database_source)

    def test_model_config_reads_environment_over_placeholders(self):
        old_env = os.environ.copy()
        try:
            os.environ["MINIMAX_API_KEY"] = "env-minimax"
            os.environ["EMBEDDING_API_KEY"] = "env-embedding"
            os.environ["GATEKEEPER_API_KEY"] = "env-gatekeeper"
            os.environ["GEMMA_API_KEY"] = "env-gemma"
            os.environ["QWEN_API_KEY"] = "env-qwen"

            import fortress_models

            reloaded = importlib.reload(fortress_models)

            self.assertEqual(reloaded.MINIMAX_API_KEY, "env-minimax")
            self.assertEqual(reloaded.EMBEDDING_API_KEY, "env-embedding")
            self.assertEqual(reloaded.GATEKEEPER_API_KEY, "env-gatekeeper")
            self.assertEqual(reloaded.GEMMA_API_KEY, "env-gemma")
            self.assertEqual(reloaded.QWEN_API_KEY, "env-qwen")
        finally:
            os.environ.clear()
            os.environ.update(old_env)
            import fortress_models

            importlib.reload(fortress_models)


if __name__ == "__main__":
    unittest.main()
