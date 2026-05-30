import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestRepoHygiene(unittest.TestCase):
    def test_gitignore_blocks_private_local_artifacts(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        required_patterns = [
            ".streamlit/secrets.toml",
            ".env",
            ".env.*",
            "*.db",
            "*.sqlite",
            "*.sqlite3",
            "*.dump",
            "*.sql",
            ".cache/",
            "models/",
            "model_cache/",
            "*.safetensors",
            "*.gguf",
            "*.onnx",
            "node_modules.broken.*/",
            "frontend/node_modules.broken.*/",
            ".claude/settings.local.json",
        ]

        for pattern in required_patterns:
            self.assertIn(pattern, gitignore)

    def test_no_private_local_artifacts_are_tracked(self):
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        )
        tracked_files = {
            path
            for path in result.stdout.decode("utf-8").split("\0")
            if path
        }

        forbidden_suffixes = (".db", ".sqlite", ".sqlite3", ".dump", ".sql")
        forbidden_exact = {
            ".streamlit/secrets.toml",
            ".env",
            ".env.local",
            ".claude/settings.local.json",
        }

        offenders = sorted(
            path
            for path in tracked_files
            if path in forbidden_exact or path.endswith(forbidden_suffixes)
        )

        self.assertEqual([], offenders)

    def test_streamlit_config_does_not_trigger_cors_xsrf_warning(self):
        config = ROOT / ".streamlit" / "config.toml"
        self.assertTrue(config.exists())

        content = config.read_text(encoding="utf-8")

        self.assertNotIn("enableCORS = false", content)

    def test_devcontainer_does_not_disable_streamlit_security_controls(self):
        config = ROOT / ".devcontainer" / "devcontainer.json"
        self.assertTrue(config.exists())

        content = config.read_text(encoding="utf-8")

        self.assertNotIn("--server.enableCORS false", content)
        self.assertNotIn("--server.enableXsrfProtection false", content)


if __name__ == "__main__":
    unittest.main()
