"""
Fortress release verification runner.

This script runs deterministic local checks instead of calling live model
providers or asserting old rule-based privacy rewrites.
"""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent

PY_COMPILE_TARGETS = [
    "app.py",
    "fortress_models.py",
    "layer0_router.py",
    "layer1_matching.py",
    "layer2_confuser.py",
    "layer3_consistency.py",
    "layer4_decoy_factory.py",
    "decoy_worker.py",
    "embedding_api.py",
    "rerank_api.py",
    "scripts/preflight_check.py",
]

CHECKS = [
    (
        "Release preflight",
        [sys.executable, "scripts/preflight_check.py"],
        ROOT,
    ),
    (
        "Python unit tests",
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        ROOT,
    ),
    (
        "Core module compile",
        [sys.executable, "-m", "py_compile", *PY_COMPILE_TARGETS],
        ROOT,
    ),
    (
        "Frontend high-severity audit",
        "npm audit --audit-level=high",
        ROOT / "frontend",
    ),
    (
        "Frontend production build",
        "npm run build",
        ROOT / "frontend",
    ),
]


def run_check(name, command, cwd):
    print("\n" + "=" * 72)
    print(f"Running: {name}")
    print("=" * 72)

    shell = isinstance(command, str)
    result = subprocess.run(command, cwd=cwd, shell=shell)

    if result.returncode != 0:
        print(f"\nFAIL: {name} exited with {result.returncode}")
        return False

    print(f"\nPASS: {name}")
    return True


def main():
    print("\n" + "=" * 72)
    print("FORTRESS - RELEASE VERIFICATION")
    print("=" * 72)

    failures = [
        name
        for name, command, cwd in CHECKS
        if not run_check(name, command, cwd)
    ]

    print("\n" + "=" * 72)
    print("VERIFICATION SUMMARY")
    print("=" * 72)

    if failures:
        print(f"Failed checks: {', '.join(failures)}")
        return 1

    print("All release verification checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
