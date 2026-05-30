# Fortress Privacy Threat Model

Fortress explores peer insight retrieval for sensitive health conversations. The system must assume that even short messages can contain identifying context, medical vulnerability, family conflict, workplace details, location hints, or crisis signals.

## Protected Assets

- Private user messages and session history.
- API keys, Supabase URLs, service-role keys, and deployment secrets.
- Raw model prompts, model responses, logs, traces, and debugging output.
- Decoy records that might still preserve identifying structure.
- User consent state, deletion requests, and contribution decisions.

## Trust Boundaries

- Browser and Streamlit UI.
- Application server and local runtime.
- Model provider APIs for chat, embeddings, reranking, and decoy generation.
- Supabase persistence for private sessions and shared decoys.
- GitHub repository, CI logs, issue reports, pull requests, and release artifacts.

## Primary Threats

- Re-identification through rare combinations of symptoms, demographics, location, timing, occupation, or relationship context.
- Secret exposure through committed files, screenshots, terminal logs, CI output, or browser traces.
- Unsafe medical behavior, including false reassurance, diagnostic claims, or missing emergency escalation.
- Public decoy pool poisoning through spam, prompt injection, hostile narratives, or misleading medical claims.
- Retrieval mismatch where a superficially similar decoy is shown for a materially different medical or emotional context.
- Consent failure where a user did not understand that an anonymized decoy could be stored for shared retrieval.

## Current Mitigations

- Model and infrastructure settings are configurable through environment variables or Streamlit secrets.
- Local heavyweight embeddings have been replaced with a remote embedding API path.
- A Gatekeeper reranker checks candidate matches after vector recall.
- Email relay UI and backend paths are disabled pending medical privacy review.
- Tests scan source files for common live-secret prefixes and verify OSS readiness artifacts.
- Documentation requires synthetic data in issues, tests, examples, and pull requests.

## Medical Safety

Fortress is not a medical device and must not present itself as a diagnostic, treatment, triage, or emergency system. Medical-safety work should prioritize clear boundaries, crisis routing, and refusal or handoff behavior for acute risks.

High-risk cases include:

- Self-harm, suicide, violence, or abuse.
- Acute symptoms that may require urgent care.
- Medication changes, pregnancy complications, or dangerous interactions.
- Requests for diagnosis, treatment plans, or reassurance that care is unnecessary.

## Open Questions

- What minimum consent text is needed before a decoy can enter the shared pool?
- How should users delete decoys that were derived from their private messages?
- What similarity threshold is safe enough for health-adjacent peer insight retrieval?
- Which fields should never be retained, even in decoy form?
- How should model-provider logging policies be surfaced to users?

## Review Checklist

- Does the change reduce private data exposure by default?
- Does it avoid storing raw health narratives unless strictly necessary?
- Does it preserve synthetic-only examples in public artifacts?
- Does it keep medical boundaries clear and conservative?
- Does it fail closed for privacy-sensitive operations?
