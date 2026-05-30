# Security Policy

Fortress is a research prototype for privacy-preserving peer insight retrieval. Treat all real user conversations, health details, API keys, database URLs, and deployment secrets as sensitive.

## Supported Versions

The project is pre-release. Security fixes target the current `main` branch unless a release branch is explicitly published.

## Reporting a Vulnerability

Please do not open public issues containing secrets, private health data, database exports, or reproduction steps that expose another person's information.

For now, report vulnerabilities privately to the repository owner through GitHub account contact channels. Include:

- A short description of the issue.
- Impact and affected component.
- Minimal reproduction steps using synthetic data.
- Whether any secret, token, or user data may have been exposed.

## Sensitive Data Rules

- Never commit API keys, GitHub tokens, Supabase keys, Streamlit secrets, or `.env` files.
- Never commit real patient, clinician, workplace, or family health narratives.
- Use synthetic examples in tests, issues, pull requests, and documentation.
- Rotate any credential that appears in source, logs, screenshots, chat transcripts, or Git history.

## Medical Safety Scope

Fortress is not a medical device and is not suitable for emergency, diagnostic, or treatment decisions. Security reports involving unsafe medical advice, crisis handling, or re-identification risk are in scope.

## Current Hardening Priorities

- Secret management and key rotation.
- Public decoy pool abuse controls.
- Consent and data deletion workflows.
- Emergency and self-harm routing.
- Privacy evaluation for decoy generation.
