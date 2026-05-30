## What Changed

Describe the change and the user-visible behavior it affects.

## Why It Matters

Explain why this improves Fortress, especially if it touches privacy, retrieval, decoy generation, or medical-safety boundaries.

## Validation

- [ ] I ran `python -m unittest discover -s tests -v`.
- [ ] I ran the relevant syntax or smoke checks for touched Python modules.
- [ ] I used synthetic examples only.

## Fortress Safety Checklist

- [ ] No API keys, tokens, Supabase secrets, Streamlit secrets, or private deployment values are included.
- [ ] No real patient, clinician, family, workplace, or health narratives are included.
- [ ] Medical language keeps Fortress framed as a research prototype, not a diagnosis or treatment tool.
- [ ] Changes to decoy generation, matching, or reranking include a privacy/relevance rationale.
- [ ] Changes to storage, logs, or telemetry avoid retaining private health details by default.
