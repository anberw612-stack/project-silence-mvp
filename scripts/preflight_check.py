#!/usr/bin/env python3
"""Local release safety checks for Fortress.

This script is intentionally conservative and read-only. It catches the easy
mistakes before publishing or submitting an OSS application.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/codeql.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/privacy_safety_review.yml",
    ".streamlit/secrets.example.toml",
    "docs/architecture.md",
    "docs/roadmap.md",
    "docs/privacy-threat-model.md",
    "docs/data-handling.md",
    "docs/evaluation-plan.md",
    "docs/public-release-checklist.md",
    "docs/openai-oss-application.md",
    "docs/publish-candidate-branch.md",
]

FORBIDDEN_TRACKED_FILES = {
    ".env",
    ".env.local",
    ".claude/settings.local.json",
    ".streamlit/secrets.toml",
    "confuser_conversations.db",
}

FORBIDDEN_TRACKED_SUFFIXES = (
    ".db",
    ".sqlite",
    ".sqlite3",
    ".dump",
    ".sql",
)

FORBIDDEN_MODEL_PATH_PREFIXES = (
    ".cache/huggingface/",
    "huggingface/",
    "model_cache/",
    "models/",
    "sentence_transformers/",
)

FORBIDDEN_MODEL_SUFFIXES = (
    ".bin",
    ".gguf",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
)

MAX_TRACKED_FILE_BYTES = 5 * 1024 * 1024

SECRET_PATTERNS = {
    "OpenAI-compatible API key": re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    "Google API key": re.compile(("AI" + "za") + r"[A-Za-z0-9_-]{16,}"),
    "GitHub token": re.compile(("ghp" + "_") + r"[A-Za-z0-9_]{16,}"),
}

TOKENIZED_REMOTE_PATTERNS = {
    "GitHub token": re.compile(("ghp" + "_") + r"[A-Za-z0-9_]{16,}"),
    "credentialed HTTPS remote": re.compile(r"https?://[^/\s]+@"),
    "x-access-token remote": re.compile(r"x-access-token", re.IGNORECASE),
}

SKIP_SECRET_SCAN_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".lock",
}

UNSAFE_DEVCONTAINER_FLAGS = (
    "--server.enableCORS false",
    "--server.enableXsrfProtection false",
)


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [path for path in result.stdout.decode("utf-8").split("\0") if path]


def git_remote_urls() -> list[str]:
    result = subprocess.run(
        ["git", "remote", "-v"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [line for line in result.stdout.decode("utf-8").splitlines() if line]


def check_required_files() -> list[str]:
    return [
        f"Missing required OSS readiness file: {path}"
        for path in REQUIRED_FILES
        if not (ROOT / path).exists()
    ]


def check_tracked_private_files(tracked_files: list[str]) -> list[str]:
    offenders = sorted(
        path
        for path in tracked_files
        if path in FORBIDDEN_TRACKED_FILES or path.endswith(FORBIDDEN_TRACKED_SUFFIXES)
    )
    return [f"Private local artifact is tracked by Git: {path}" for path in offenders]


def check_git_remote_urls(remote_urls: list[str]) -> list[str]:
    errors: list[str] = []
    for url in remote_urls:
        if any(pattern.search(url) for pattern in TOKENIZED_REMOTE_PATTERNS.values()):
            errors.append("Git remote URL appears to contain a token or credential")
    return errors


def check_tracked_model_artifacts(tracked_files: list[str]) -> list[str]:
    offenders = sorted(
        path
        for path in tracked_files
        if path.startswith(FORBIDDEN_MODEL_PATH_PREFIXES)
        or path.lower().endswith(FORBIDDEN_MODEL_SUFFIXES)
    )
    return [f"Model/cache artifact is tracked by Git: {path}" for path in offenders]


def check_tracked_large_files(tracked_files: list[str], size_lookup=None) -> list[str]:
    using_default_lookup = size_lookup is None
    if size_lookup is None:
        size_lookup = lambda path: (ROOT / path).stat().st_size

    errors: list[str] = []
    for path in tracked_files:
        full_path = ROOT / path
        if using_default_lookup and not full_path.exists():
            continue
        try:
            size = size_lookup(path)
        except FileNotFoundError:
            continue

        if size > MAX_TRACKED_FILE_BYTES:
            errors.append(f"Tracked file is larger than 5 MiB: {path}")
    return errors


def should_scan_for_secrets(path: str) -> bool:
    file_path = Path(path)
    if file_path.suffix.lower() in SKIP_SECRET_SCAN_SUFFIXES:
        return False
    if path.startswith("venv/") or path.startswith("frontend/node_modules/"):
        return False
    return True


def check_secret_patterns(tracked_files: list[str]) -> list[str]:
    errors: list[str] = []
    for path in tracked_files:
        if not should_scan_for_secrets(path):
            continue

        full_path = ROOT / path
        try:
            content = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                errors.append(f"{label} pattern found in tracked file: {path}")

    return errors


def check_unsafe_devcontainer_flags(content: str | None = None) -> list[str]:
    if content is None:
        config_path = ROOT / ".devcontainer" / "devcontainer.json"
        if not config_path.exists():
            return []
        content = config_path.read_text(encoding="utf-8")

    return [
        f"Devcontainer disables Streamlit security control: {flag}"
        for flag in UNSAFE_DEVCONTAINER_FLAGS
        if flag in content
    ]


def run_checks() -> list[str]:
    tracked_files = git_ls_files()
    errors: list[str] = []
    errors.extend(check_required_files())
    errors.extend(check_tracked_private_files(tracked_files))
    errors.extend(check_git_remote_urls(git_remote_urls()))
    errors.extend(check_tracked_model_artifacts(tracked_files))
    errors.extend(check_tracked_large_files(tracked_files))
    errors.extend(check_secret_patterns(tracked_files))
    errors.extend(check_unsafe_devcontainer_flags())
    return errors


def main() -> int:
    errors = run_checks()
    if errors:
        print("Preflight checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Preflight checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
