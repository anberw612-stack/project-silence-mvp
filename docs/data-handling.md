# Fortress Data Handling Guide

Fortress is an early research prototype for privacy-preserving peer insight retrieval in sensitive health conversations. This guide describes the intended data boundaries for development and public review. It is not a production privacy policy.

## Data Categories

- Private conversation text: user messages, assistant responses, and session context.
- Derived decoys: anonymized or narrative-shifted versions of sensitive stories intended for retrieval experiments.
- Retrieval metadata: embeddings, similarity scores, reranker decisions, batch IDs, source IDs, and topic tags.
- Configuration secrets: model-provider keys, Supabase URLs, Supabase keys, Streamlit secrets, and GitHub tokens.
- Local development artifacts: SQLite files, logs, screenshots, caches, model downloads, and frontend build output.

## Consent

Fortress should not treat a private message as consent to publish, share, or reuse a derived decoy. The MVP still needs an explicit consent flow before any user-derived decoy enters a shared retrieval pool.

Until that flow exists:

- Use synthetic data in tests, docs, issues, pull requests, demos, and screenshots.
- Treat shared decoy generation as experimental.
- Avoid using real patient, clinician, workplace, family, or location-specific narratives.
- Document any code path that stores or shares derived content.

## Model Provider Boundaries

Fortress currently uses remote model-provider APIs for chat, embeddings, reranking, and decoy generation. That means sensitive text may leave the application runtime when those providers are called.

Before production use, contributors should verify and document:

- Which provider receives which prompt or text field.
- Whether the provider logs, stores, or trains on requests.
- Whether the provider supports data retention controls.
- Whether requests include direct identifiers or avoidable context.
- How provider failures are handled without exposing extra private context.

## Retention

The current MVP does not yet define production-grade retention windows. Treat all local and Supabase-stored development data as sensitive and temporary.

Current expectations:

- Do not commit local databases, logs, exports, or `.streamlit/secrets.toml`.
- Do not retain raw private health narratives in test fixtures.
- Prefer synthetic records for demos and automated checks.
- Keep debug output from printing full private prompts or model responses.

## Deletion

Deletion is a required product capability before broader use. The project still needs a user-facing deletion workflow for private sessions and any user-derived decoys.

Until deletion is implemented:

- Do not promise permanent user control over already-generated shared decoys.
- Avoid collecting real user-derived decoys outside controlled development.
- Keep the roadmap issue for deletion and data export visible.

## Logging and Screenshots

Logs and screenshots can expose secrets or private health details even when code is clean.

- Redact API keys, Supabase values, browser tabs, account names, and prompt text before sharing screenshots.
- Avoid copying raw model prompts or responses into issues.
- Use summaries with synthetic examples when reporting bugs.

## Public Repository Rules

- Public issues and pull requests must use synthetic data only.
- Security reports with secrets or private health details should not be filed publicly.
- CI and preflight checks should fail if local database files, model weights, large artifacts, or common secret prefixes are tracked.
- Contributors should run `python scripts/preflight_check.py` before publishing branches or release candidates.
