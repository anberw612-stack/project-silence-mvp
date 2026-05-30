import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestOssReadiness(unittest.TestCase):
    def test_ci_workflow_runs_python_tests(self):
        workflow = ROOT / ".github" / "workflows" / "ci.yml"

        self.assertTrue(workflow.exists())

        content = workflow.read_text(encoding="utf-8")
        self.assertIn("permissions:", content)
        self.assertIn("contents: read", content)
        self.assertIn("python -m unittest discover -s tests -v", content)
        self.assertIn("python -m py_compile", content)
        self.assertIn("python scripts/preflight_check.py", content)
        self.assertIn("actions/setup-node", content)
        self.assertIn("npm ci", content)
        self.assertIn("npm audit --audit-level=high", content)
        self.assertIn("npm run build", content)

    def test_frontend_lockfile_exists_for_reproducible_ci_builds(self):
        package_json = ROOT / "frontend" / "package.json"
        package_lock = ROOT / "frontend" / "package-lock.json"
        node_version = ROOT / ".nvmrc"

        self.assertTrue(package_json.exists())
        self.assertTrue(package_lock.exists())
        self.assertTrue(node_version.exists())

        package_content = package_json.read_text(encoding="utf-8")

        self.assertIn('"name": "fortress-frontend"', package_content)
        self.assertIn('"engines":', package_content)
        self.assertIn('"node": "20.x"', package_content)
        self.assertEqual("20", node_version.read_text(encoding="utf-8").strip())
        self.assertIn(
            '"build": "CHOKIDAR_USEPOLLING=true node node_modules/vite/bin/vite.js build"',
            package_content,
        )
        self.assertIn('"@vitejs/plugin-react": "^4.', package_content)
        self.assertNotIn('"@vitejs/plugin-react": "^5.', package_content)
        self.assertIn('"vite": "^4.', package_content)
        self.assertNotIn('"vite": "^5.', package_content)
        self.assertNotIn('"vite": "^6.', package_content)
        self.assertNotIn('"vite": "^7.', package_content)
        self.assertNotIn('"vite": "^8.', package_content)
        self.assertIn('"overrides":', package_content)
        self.assertIn('"esbuild": "^0.25.12"', package_content)
        self.assertIn('"name": "fortress-frontend"', package_lock.read_text(encoding="utf-8"))

    def test_vite_build_disables_unstable_minifier_for_ci(self):
        vite_config = ROOT / "frontend" / "vite.config.js"

        content = vite_config.read_text(encoding="utf-8")

        self.assertIn("minify: false", content)

    def test_public_frontend_uses_fortress_brand_without_compliance_overclaims(self):
        public_frontend_files = [ROOT / "frontend" / "index.html"]
        public_frontend_files.extend((ROOT / "frontend" / "src").rglob("*.jsx"))
        public_frontend_files.extend((ROOT / "frontend" / "src").rglob("*.css"))

        for path in public_frontend_files:
            content = path.read_text(encoding="utf-8")
            normalized = content.lower()

            self.assertNotIn("HOTFIX", content, f"Debug hotfix marker found in {path}")
            self.assertNotIn("DEBUG MODE", content, f"Debug mode marker found in {path}")
            self.assertNotIn("FORCE RED", content, f"Debug color marker found in {path}")
            self.assertNotIn("console.log", content, f"Console logging found in public frontend file {path}")
            self.assertNotIn("console.error", content, f"Console error logging found in public frontend file {path}")
            self.assertNotIn("confuser", normalized, f"Deprecated public brand found in {path}")
            self.assertNotIn("full compliance", normalized, f"Compliance overclaim found in {path}")
            self.assertNotIn("all jurisdictions", normalized, f"Compliance overclaim found in {path}")
            self.assertNotIn("military-grade", normalized, f"Security overclaim found in {path}")
            self.assertNotIn("biometric", normalized, f"Unsupported feature claim found in {path}")
            self.assertNotIn("on-device", normalized, f"Unsupported architecture claim found in {path}")
            self.assertNotIn("never leaves", normalized, f"Unsupported data-flow claim found in {path}")
            self.assertNotIn("enterprise-grade", normalized, f"Security overclaim found in {path}")
            self.assertNotIn("256-bit", normalized, f"Unsupported encryption claim found in {path}")
            self.assertNotIn("data breaches", normalized, f"Unsupported incident-history claim found in {path}")
            self.assertNotIn("pricing", normalized, f"Commercial navigation found in {path}")
            self.assertNotIn("get started", normalized, f"Product-launch CTA found in {path}")
            self.assertNotIn("contact sales", normalized, f"Sales CTA found in {path}")
            self.assertNotIn('href="#contact"', normalized, f"Dead contact anchor found in {path}")

        navbar_content = (ROOT / "frontend" / "src" / "components" / "Navbar.jsx").read_text(encoding="utf-8")
        self.assertIn("GitHub", navbar_content)
        self.assertIn("Roadmap", navbar_content)
        self.assertIn("Docs", navbar_content)

    def test_current_entrypoints_do_not_use_legacy_confuser_brand(self):
        current_entrypoints = [
            ROOT / "app.py",
            ROOT / "main.py",
            ROOT / "verify_mvp.py",
        ]

        for path in current_entrypoints:
            content = path.read_text(encoding="utf-8")

            self.assertNotIn("Confuser MVP", content, f"Legacy product name found in {path}")
            self.assertNotIn("CONFUSER MVP", content, f"Legacy product name found in {path}")
            self.assertNotIn("Confuser system", content, f"Legacy system name found in {path}")

        app_content = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("APP STARTED", app_content)
        self.assertNotIn("CODE VERSION", app_content)

        verify_content = (ROOT / "verify_mvp.py").read_text(encoding="utf-8")
        self.assertIn("scripts/preflight_check.py", verify_content)
        self.assertIn("unittest", verify_content)
        self.assertIn("py_compile", verify_content)
        self.assertIn("npm audit --audit-level=high", verify_content)
        self.assertIn("npm run build", verify_content)
        self.assertNotIn("SemanticMatcher", verify_content)
        self.assertNotIn("perturb_text", verify_content)
        self.assertNotIn("Seattle", verify_content)
        self.assertNotIn("Austin", verify_content)

    def test_public_governance_docs_exist(self):
        code_of_conduct = ROOT / "CODE_OF_CONDUCT.md"
        release_checklist = ROOT / "docs" / "public-release-checklist.md"

        for path in (code_of_conduct, release_checklist):
            self.assertTrue(path.exists(), f"Missing public governance doc: {path}")

        conduct_content = code_of_conduct.read_text(encoding="utf-8")
        checklist_content = release_checklist.read_text(encoding="utf-8")

        self.assertIn("private health", conduct_content)
        self.assertIn("medical", conduct_content.lower())
        self.assertIn("Rotate", checklist_content)
        self.assertIn("OpenAI Codex for OSS", checklist_content)

    def test_security_automation_configs_exist(self):
        dependabot = ROOT / ".github" / "dependabot.yml"
        codeql = ROOT / ".github" / "workflows" / "codeql.yml"

        for path in (dependabot, codeql):
            self.assertTrue(path.exists(), f"Missing security automation config: {path}")

        dependabot_content = dependabot.read_text(encoding="utf-8")
        codeql_content = codeql.read_text(encoding="utf-8")

        self.assertIn('package-ecosystem: "pip"', dependabot_content)
        self.assertIn('package-ecosystem: "npm"', dependabot_content)
        self.assertIn('package-ecosystem: "github-actions"', dependabot_content)
        self.assertIn("github/codeql-action/init", codeql_content)
        self.assertIn("security-events: write", codeql_content)

    def test_openai_oss_application_draft_exists(self):
        draft = ROOT / "docs" / "openai-oss-application.md"

        self.assertTrue(draft.exists())

        content = draft.read_text(encoding="utf-8")
        self.assertIn("Why does this repository qualify?", content)
        self.assertIn("How will you use API credits?", content)
        self.assertIn("Fortress", content)
        self.assertIn("CodeQL", content)
        self.assertIn("Dependabot", content)
        self.assertIn("preflight", content)
        self.assertIn("data-handling", content)
        self.assertIn("evaluation plan", content)

    def test_publish_candidate_guide_exists(self):
        guide = ROOT / "docs" / "publish-candidate-branch.md"

        self.assertTrue(guide.exists())

        content = guide.read_text(encoding="utf-8")

        self.assertIn("codex/oss-readiness-hardening", content)
        self.assertIn("git push -u origin codex/oss-readiness-hardening", content)
        self.assertIn("python verify_mvp.py", content)
        self.assertIn("confuser_conversations.db", content)
        self.assertIn(".claude/settings.local.json", content)
        self.assertIn("node_modules.broken", content)
        self.assertIn("OpenAI Codex for OSS", content)
        self.assertIn("docs/openai-oss-application.md", content)

    def test_legacy_design_docs_are_clearly_marked_historical(self):
        legacy_docs = [
            ROOT / "ARCHITECTURE_UPGRADE.md",
            ROOT / "CONFUSER_LLM_UPGRADE.md",
            ROOT / "CONFUSER_WEB_APP.md",
            ROOT / "VISION.md",
        ]

        for path in legacy_docs:
            content = path.read_text(encoding="utf-8")

            self.assertIn("Legacy design note", content, f"Missing legacy banner in {path}")
            self.assertIn("current Fortress", content, f"Missing current-project caveat in {path}")
            self.assertIn("canonical public documentation", content, f"Missing canonical-doc pointer in {path}")
            self.assertNotIn("DeepSeek", content, f"Retired provider name found in public legacy doc {path}")

    def test_public_maintainer_templates_exist(self):
        pr_template = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
        privacy_issue = ROOT / ".github" / "ISSUE_TEMPLATE" / "privacy_safety_review.yml"
        bug_issue = ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"

        for path in (pr_template, privacy_issue, bug_issue):
            self.assertTrue(path.exists(), f"Missing OSS maintainer template: {path}")

        pr_content = pr_template.read_text(encoding="utf-8").lower()
        self.assertIn("privacy", pr_content)
        self.assertIn("medical", pr_content)

    def test_public_roadmap_and_threat_model_exist(self):
        architecture = ROOT / "docs" / "architecture.md"
        roadmap = ROOT / "docs" / "roadmap.md"
        threat_model = ROOT / "docs" / "privacy-threat-model.md"
        data_handling = ROOT / "docs" / "data-handling.md"
        evaluation_plan = ROOT / "docs" / "evaluation-plan.md"

        for path in (architecture, roadmap, threat_model, data_handling, evaluation_plan):
            self.assertTrue(path.exists(), f"Missing OSS readiness doc: {path}")

        architecture_content = architecture.read_text(encoding="utf-8")
        roadmap_content = roadmap.read_text(encoding="utf-8")
        threat_content = threat_model.read_text(encoding="utf-8")
        data_content = data_handling.read_text(encoding="utf-8")
        evaluation_content = evaluation_plan.read_text(encoding="utf-8")

        self.assertIn("Layer 0", architecture_content)
        self.assertIn("Layer 1", architecture_content)
        self.assertIn("Layer 4", architecture_content)
        self.assertIn("Gatekeeper", architecture_content)
        self.assertIn("Supabase", architecture_content)
        self.assertIn("Model Provider Boundaries", architecture_content)
        self.assertIn("Privacy-Masked Response", architecture_content)
        self.assertNotIn("Confuser Response", architecture_content)
        self.assertIn("Phase 1", roadmap_content)
        self.assertIn("Fortress", roadmap_content)
        self.assertIn("Protected Assets", threat_content)
        self.assertIn("Medical Safety", threat_content)
        self.assertIn("Consent", data_content)
        self.assertIn("Retention", data_content)
        self.assertIn("Deletion", data_content)
        self.assertIn("Model Provider Boundaries", data_content)
        self.assertIn("Synthetic Evaluation", evaluation_content)
        self.assertIn("Privacy Leakage", evaluation_content)
        self.assertIn("Retrieval Relevance", evaluation_content)
        self.assertIn("Medical Safety", evaluation_content)


if __name__ == "__main__":
    unittest.main()
