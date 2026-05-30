# Fortress

Fortress is an open-source prototype for privacy-preserving peer insight retrieval in sensitive health conversations.

The project explores a simple question: can people learn from similar lived experiences without exposing the identity behind those experiences? Fortress answers with a decoy-first pipeline: private conversations remain private, while anonymized parallel versions can become searchable peer insights.

> Research prototype: Fortress is not a medical device and does not provide diagnosis, treatment, or emergency support.

## Why This Matters

Sensitive health questions often contain enough context to identify a person: age, hospital, job, diagnosis, family pressure, location, timing, and emotional state. Traditional redaction can remove too much useful meaning. Fortress instead experiments with narrative masking: preserving the abstract dilemma while changing the identifying surface.

## Current Architecture

1. **Privacy router**
   Classifies incoming messages and decides whether privacy protection should run.

2. **Remote embedding recall**
   Uses SiliconFlow-compatible `BAAI/bge-m3` embeddings to find candidate peer insights without loading local model weights.

3. **Reranker Gatekeeper**
   Uses `Qwen/Qwen3-Reranker-8B` through a rerank API to validate whether candidates represent the same core dilemma before they are shown.

4. **AI response**
   Generates the direct assistant response through the configured chat model.

5. **Cascading decoy generation**
   Generates up to five anonymized decoys using Gemma first, Qwen as fallback, and a rescue mode for malformed outputs.

6. **Supabase persistence**
   Stores private sessions separately from the shared `global_decoys` pool.

## Status

Fortress is an early MVP. The core pipeline runs, but the project is still being hardened for medical privacy, open-source maintenance, and public evaluation.

Known high-priority work:

- Move all secrets into deployment secrets or environment variables.
- Add explicit consent before contributing anonymized decoys.
- Add emergency and high-risk medical routing.
- Add moderation and abuse controls for the public decoy pool.
- Replace prototype database schema strings with migrations.
- Add a stronger evaluation set for privacy, relevance, and decoy quality.

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the example secrets file and fill it locally:

```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

Required model configuration can also be supplied as environment variables:

```bash
MINIMAX_API_KEY=...
EMBEDDING_API_KEY=...
GATEKEEPER_API_KEY=...
GEMMA_API_KEY=...
QWEN_API_KEY=...
```

Run the Streamlit app:

```bash
streamlit run app.py
```

## Tests

Run the unit tests:

```bash
python -m unittest discover -s tests -v
```

Run a syntax check over the core modules:

```bash
python -m py_compile app.py fortress_models.py layer0_router.py layer1_matching.py layer4_decoy_factory.py rerank_api.py embedding_api.py
```

Run the local preflight check before publishing or submitting an OSS application:

```bash
python scripts/preflight_check.py
```

## Open Source Maintenance

This repository is being prepared for public open-source review. Please do not commit secrets, private health data, or production database exports.

Useful files:

- [SECURITY.md](SECURITY.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/roadmap.md](docs/roadmap.md)
- [docs/privacy-threat-model.md](docs/privacy-threat-model.md)
- [docs/data-handling.md](docs/data-handling.md)
- [docs/evaluation-plan.md](docs/evaluation-plan.md)
- [docs/public-release-checklist.md](docs/public-release-checklist.md)
- [docs/openai-oss-application.md](docs/openai-oss-application.md)
- [.streamlit/secrets.example.toml](.streamlit/secrets.example.toml)

## License

Apache License 2.0. See [LICENSE](LICENSE).
