# OpenAI Codex for Open Source Application Draft

Form: https://openai.com/form/codex-for-oss/

## Repository

https://github.com/anberw612-stack/project-silence-mvp

## Role

Primary maintainer.

## Why does this repository qualify?

Fortress is an open-source research prototype for privacy-preserving peer insight retrieval in sensitive health conversations. It explores narrative masking, decoy generation, remote semantic recall, Gatekeeper reranking, and Supabase-backed decoy persistence so people can learn from similar experiences without exposing identity. The repo is early, but it targets a high-importance privacy problem for health, mental health, and safety-sensitive communities.

Current OSS readiness evidence:

- CI runs Python tests, frontend build, high-severity npm audit, release preflight, and core syntax checks.
- CodeQL and Dependabot are configured.
- A local preflight check blocks tracked secrets, local databases, tokenized remotes, model weights, and large artifacts.
- Documentation now includes architecture, threat model, data-handling guide, evaluation plan, roadmap, security policy, contribution guide, and code of conduct.

Character count for form answer above: 460

## I'm interested in

- Codex Security
- API credits for my project

## How will you use API credits?

We will use API credits to maintain Fortress as an OSS privacy prototype: automated code review, security hardening, regression tests, release workflows, decoy quality evaluation, and maintainer automation for issues and pull requests. Credits will also support synthetic evaluation runs that measure retrieval relevance, privacy leakage, medical-safety boundaries, and failure cases without using real patient data.

Character count: 416

## Anything else we should know?

Fortress is not a medical device and does not provide diagnosis, treatment, triage, or emergency support. The public roadmap prioritizes consent, deletion, emergency routing, public decoy-pool abuse controls, and synthetic evaluation before broader use. The project now has CodeQL, Dependabot, CI, preflight checks, data-handling documentation, and an evaluation plan to make review safer.

Character count: 389

## Pre-Submission Checklist

- Rotate any API keys or GitHub tokens that appeared in source, screenshots, logs, or Git history.
- Confirm GitHub profile visibility is public.
- Confirm repository visibility is public.
- Confirm README, LICENSE, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, architecture, data-handling, evaluation plan, and release checklist are pushed.
- Confirm CI, CodeQL, Dependabot, issue templates, PR template, and preflight checks are pushed.
- Run `python scripts/preflight_check.py`.
- Run `cd frontend && npm ci && npm audit --audit-level=high && npm run build`.
- Run `python -m unittest discover -s tests -v`.
- Consider publishing a `v0.1.0` release before submitting.
- Open at least a small set of GitHub issues for the roadmap so maintenance activity is visible.
