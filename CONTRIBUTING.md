# Contributing

Thanks for helping improve Fortress. This project is still early, so the most valuable contributions are careful, small, and safety-aware.

## Project Direction

Fortress is focused on privacy-preserving peer insight retrieval for sensitive health conversations. Changes should preserve these principles:

- Protect user identity before improving convenience.
- Use synthetic data in examples and tests.
- Prefer explicit safety boundaries over silent behavior.
- Keep model provider details configurable.

## Development Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
streamlit run app.py
```

Fill local secrets with your own test credentials. Do not commit `.streamlit/secrets.toml`.

## Before Opening a Pull Request

Run:

```bash
python -m unittest discover -s tests -v
python -m py_compile app.py fortress_models.py layer0_router.py layer1_matching.py layer4_decoy_factory.py rerank_api.py embedding_api.py
python scripts/preflight_check.py
```

Also scan your diff for credentials and real private data.

## Useful Contribution Areas

- Medical safety routing and emergency handoff.
- Consent, deletion, and data export workflows.
- Decoy quality evaluation.
- Abuse prevention for the shared decoy pool.
- Test coverage for retrieval and decoy generation.
- Documentation that makes the system easier to audit.

## Pull Request Style

- Keep PRs focused.
- Explain the behavior change and why it matters.
- Include tests for shared logic or safety-sensitive behavior.
- Use synthetic examples only.
