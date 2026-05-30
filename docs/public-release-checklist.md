# Fortress Public Release Checklist

Use this checklist before making the repository public, publishing a release, or submitting the OpenAI Codex for OSS form.

## 1. Rotate Exposed Secrets

- Rotate every API key, GitHub token, Supabase key, Streamlit secret, and model-provider key that appeared in source, screenshots, chat transcripts, logs, browser windows, or Git history.
- Confirm local `.streamlit/secrets.toml` is ignored and not tracked.
- Confirm Git remotes do not contain embedded credentials.
- Run `python scripts/preflight_check.py`.

## 2. Verify Repository Hygiene

- Confirm `confuser_conversations.db` and other local database files are not tracked.
- Confirm no real private health data appears in tests, docs, issues, pull requests, screenshots, or example prompts.
- Confirm local model caches, downloaded weights, `frontend/node_modules/`, and `frontend/dist/` are ignored.
- Run the full test suite and frontend build:

```bash
python -m unittest discover -s tests -v
python -m py_compile app.py fortress_models.py layer0_router.py layer1_matching.py layer2_confuser.py layer3_consistency.py layer4_decoy_factory.py decoy_worker.py embedding_api.py rerank_api.py scripts/preflight_check.py
cd frontend && npm ci && npm audit --audit-level=high && npm run build
```

## 3. Confirm OSS Maintenance Surface

- README, LICENSE, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, architecture, roadmap, threat model, data-handling guide, evaluation plan, and application draft are present.
- GitHub issue templates and pull request template are present.
- CI, CodeQL, and Dependabot are present.
- The repository and maintainer GitHub profile are public.

## 4. Prepare OpenAI Codex for OSS Submission

- Use `docs/openai-oss-application.md` as the form draft.
- Link to the public GitHub repository.
- Emphasize that Fortress is an open-source research prototype, not a medical device.
- Emphasize privacy-preserving peer insight retrieval, decoy generation, semantic matching, and safety hardening.
- Mention Codex use cases: code review, security hardening, tests, release workflow, synthetic evaluation, and maintainer automation.

## 5. First Public Release

- Consider tagging `v0.1.0` after CI passes on GitHub.
- Open roadmap issues for consent, deletion, emergency routing, decoy-pool abuse controls, and privacy evaluation.
- Avoid announcing broad public use until consent, deletion, and emergency handling are stronger.
