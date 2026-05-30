# Publish Candidate Branch

This guide turns the local Fortress OSS-readiness snapshot into a safe GitHub
review branch without publishing local private artifacts.

## Current Candidate

- Branch: `codex/oss-readiness-hardening`
- Purpose: OSS readiness, privacy hardening, remote model configuration, CI,
  governance docs, and OpenAI Codex for OSS application preparation.
- Application draft: `docs/openai-oss-application.md`

## Local Verification

Run the deterministic release verifier before publishing:

```bash
python verify_mvp.py
```

This runs release preflight checks, Python tests, core module compilation,
frontend high-severity audit, and the frontend production build.

## Do Not Publish Local Artifacts

The following files may exist locally but must not be committed or uploaded:

- `confuser_conversations.db`
- `.claude/settings.local.json`
- `node_modules.broken.*`
- `frontend/node_modules/`
- `frontend/dist/`
- `.streamlit/secrets.toml`
- `.env`

The candidate branch is expected to delete the tracked local database and keep
only `.streamlit/secrets.example.toml` as the public secret template.

## Push The Candidate Branch

After GitHub authentication is available locally:

```bash
git status --short --branch
git push -u origin codex/oss-readiness-hardening
```

Do not force-push `main`. Publish this candidate branch first, then review it
through a pull request.

## Pull Request Checklist

1. Open a PR from `codex/oss-readiness-hardening` into `main`.
2. Confirm GitHub Actions CI passes.
3. Confirm CodeQL starts or is queued.
4. Confirm the PR diff does not include local databases, secrets, model weights,
   `node_modules`, or build artifacts.
5. Confirm the public README, roadmap, threat model, data-handling guide,
   evaluation plan, security policy, contribution guide, and code of conduct
   render correctly.
6. Merge only after the CI and review checks are clean.

## OpenAI Codex for OSS Submission

After the PR is merged and the public repository shows the Fortress-ready docs,
submit the OpenAI Codex for OSS form using the draft in
`docs/openai-oss-application.md`.

Before submitting, rotate any API keys that appeared in screenshots, logs,
source history, or local files.
