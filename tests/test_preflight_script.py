import subprocess
import sys
import unittest
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_preflight_module():
    script = ROOT / "scripts" / "preflight_check.py"
    spec = importlib.util.spec_from_file_location("preflight_check", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestPreflightScript(unittest.TestCase):
    def test_preflight_script_runs_cleanly(self):
        script = ROOT / "scripts" / "preflight_check.py"

        self.assertTrue(script.exists(), "Missing scripts/preflight_check.py")

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        self.assertEqual(
            0,
            result.returncode,
            f"Preflight failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )
        self.assertIn("Preflight checks passed", result.stdout)

    def test_preflight_script_checks_release_blockers(self):
        script = ROOT / "scripts" / "preflight_check.py"
        self.assertTrue(script.exists(), "Missing scripts/preflight_check.py")

        content = script.read_text(encoding="utf-8")

        self.assertIn("CODE_OF_CONDUCT.md", content)
        self.assertIn("confuser_conversations.db", content)
        self.assertIn(".github/dependabot.yml", content)
        self.assertIn(".github/workflows/codeql.yml", content)
        self.assertIn(".streamlit/secrets.toml", content)
        self.assertIn("docs/architecture.md", content)
        self.assertIn("docs/public-release-checklist.md", content)
        self.assertIn("docs/data-handling.md", content)
        self.assertIn("docs/evaluation-plan.md", content)
        self.assertIn("docs/privacy-threat-model.md", content)
        self.assertIn("docs/openai-oss-application.md", content)
        self.assertIn("docs/publish-candidate-branch.md", content)
        self.assertIn(".claude/settings.local.json", content)
        self.assertIn("check_unsafe_devcontainer_flags", content)
        self.assertIn("SECRET_PATTERNS", content)

    def test_preflight_rejects_tokenized_git_remotes(self):
        preflight = load_preflight_module()

        errors = preflight.check_git_remote_urls(
            [
                "https://" + "ghp" + "_abcdef1234567890@github.com/example/repo.git",
                "https://x-access-token:secret@example.com/repo.git",
            ]
        )

        self.assertEqual(2, len(errors))
        self.assertTrue(all("Git remote URL appears to contain a token" in e for e in errors))

    def test_preflight_rejects_tracked_model_and_large_artifacts(self):
        preflight = load_preflight_module()

        model_errors = preflight.check_tracked_model_artifacts(
            [
                "models/bge-m3/config.json",
                ".cache/huggingface/hub/model.bin",
                "docs/roadmap.md",
            ]
        )
        large_errors = preflight.check_tracked_large_files(
            ["tiny.py", "large.bin"],
            size_lookup=lambda path: 6 * 1024 * 1024 if path == "large.bin" else 100,
        )

        self.assertEqual(2, len(model_errors))
        self.assertEqual(["Tracked file is larger than 5 MiB: large.bin"], large_errors)

    def test_preflight_rejects_local_agent_config_and_unsafe_devcontainer_flags(self):
        preflight = load_preflight_module()

        private_errors = preflight.check_tracked_private_files(
            [".claude/settings.local.json", "README.md"]
        )
        unsafe_errors = preflight.check_unsafe_devcontainer_flags(
            'streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false'
        )

        self.assertEqual(
            ["Private local artifact is tracked by Git: .claude/settings.local.json"],
            private_errors,
        )
        self.assertEqual(2, len(unsafe_errors))
        self.assertTrue(all("Devcontainer disables Streamlit" in e for e in unsafe_errors))


if __name__ == "__main__":
    unittest.main()
