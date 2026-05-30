# Fortress Roadmap

This roadmap is intentionally safety-first. Fortress is a research prototype for privacy-preserving peer insight retrieval in sensitive health conversations, not a medical device.

## Phase 1: Emergency Hardening

Goal: make the MVP safe enough for public review without pretending it is production-ready.

- Keep all model and database credentials outside source code.
- Replace local heavyweight embedding downloads with remote embedding API calls.
- Disable email relay flows until privacy and consent rules are designed.
- Keep model providers configurable for MiniMax, SiliconFlow, Google-compatible Gemma, and Qwen-compatible fallback paths.
- Add tests for configuration hygiene, decoy fallback behavior, and Gatekeeper filtering.
- Publish clear README, SECURITY, CONTRIBUTING, license, CI, and OSS application notes.

## Phase 2: Consent and Data Control

Goal: make user agency explicit before any story-like content can enter shared retrieval.

- Add explicit consent before creating or storing shared decoys.
- Add deletion and export workflows for private sessions and contributed decoys.
- Add retention controls for logs, model responses, and Supabase records.
- Add database migrations instead of prototype schema assumptions.
- Add a privacy review checklist for every storage or telemetry change.

## Phase 3: Medical Safety and Abuse Resistance

Goal: make the system less likely to amplify unsafe advice or expose vulnerable users.

- Add emergency, self-harm, and acute medical risk routing.
- Add a medical-boundary response layer that avoids diagnosis, treatment plans, and false reassurance.
- Add abuse controls for public decoy pool poisoning, spam, and adversarial prompt injection.
- Add synthetic evaluation sets for relevance, privacy preservation, hallucination risk, and retrieval mismatch.
- Add monitoring that reports aggregate quality signals without retaining private health narratives.

## Phase 4: Public Evaluation

Goal: make Fortress auditable by outside contributors before broader use.

- Publish an evaluation methodology for decoy quality and re-identification risk.
- Add example notebooks or scripts using synthetic data only.
- Add issue labels for privacy, medical safety, model behavior, and infrastructure.
- Publish a `v0.1.0` release after secrets are rotated and the repository is public.
- Collect early contributor feedback on the threat model and roadmap.

## Non-Goals for the MVP

- Fortress will not provide diagnosis, treatment, emergency response, or clinician replacement.
- Fortress will not store real patient examples in tests, documentation, or public issues.
- Fortress will not optimize engagement at the expense of privacy, consent, or safety boundaries.
