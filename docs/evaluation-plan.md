# Fortress Evaluation Plan

Fortress needs synthetic evaluation before it should be trusted with broader sensitive-health use. This plan defines what to measure for decoy generation, semantic retrieval, reranking, and medical-safety boundaries.

## Synthetic Evaluation Only

Initial evaluation must use synthetic stories only. Test cases should be fictional and should avoid real patient, clinician, workplace, family, location, or timing details.

Each synthetic case should include:

- A private-style source message.
- Expected sensitive attributes that must not survive in a decoy.
- The abstract dilemma that should be preserved.
- Near-match and non-match retrieval candidates.
- A medical-safety label when relevant.

## Privacy Leakage

Decoys should preserve the abstract experience while removing identifying surface details.

Reviewers should check:

- Direct identifiers: names, exact locations, employers, schools, clinicians, hospitals, emails, phone numbers, usernames.
- Rare combinations: age plus diagnosis plus location, unusual occupation plus timing, family structure plus rare condition.
- Temporal anchors: exact dates, recent events, appointment times, local incidents.
- Verbatim carryover: long copied phrases from the source message.
- Provider artifacts: model refusals, prompt fragments, or debug text leaked into stored decoys.

Minimum expected result for public demos: no direct identifiers and no obvious rare identifying combinations in generated decoys.

## Retrieval Relevance

Vector recall should find potentially similar stories, but the Gatekeeper should reject false friends.

Evaluate:

- Precision: top matches share the same core dilemma, not just overlapping medical words.
- Recall: known near-matches are surfaced before unrelated decoys.
- False positives: semantically different conditions or risks are not presented as strong matches.
- Layering: Deja vu, Resonance, and Precision labels match the final similarity evidence.
- Cross-language behavior: Chinese and English examples do not collapse unrelated contexts.

Minimum expected result for public demos: obvious non-matches are filtered or downgraded by the Gatekeeper.

## Decoy Utility

A decoy is useful only if it remains emotionally and practically recognizable after anonymization.

Reviewers should score:

- Core dilemma preserved.
- Emotional tone preserved without copying exact language.
- Medical facts generalized enough to reduce identification risk.
- Story remains coherent and searchable.
- Output is valid JSON with required fields.

## Medical Safety

Fortress is not a medical device. Evaluation should verify that matches and responses do not imply diagnosis, treatment, triage, or emergency reassurance.

High-risk synthetic cases should include:

- Self-harm or suicide signals.
- Acute symptoms that may require urgent care.
- Medication changes, pregnancy complications, or dangerous interactions.
- Requests for diagnosis, treatment plans, or reassurance that care is unnecessary.

Minimum expected result for public demos: high-risk cases should trigger conservative boundaries or handoff language, not peer-story substitution alone.

## Failure Logging

Failed generations and mismatches are valuable only when logged without private data.

Track aggregate counts for:

- Invalid JSON.
- Missing required fields.
- Rescue-mode decoys.
- Gatekeeper mismatch.
- Low-confidence partial match.
- Medical-safety boundary triggered.

Do not store raw private prompts in public evaluation artifacts.

## Release Gate

Before a broader public release, Fortress should have a synthetic evaluation set that covers privacy leakage, retrieval relevance, decoy utility, and medical safety. The evaluation should be repeatable without real private health data.
