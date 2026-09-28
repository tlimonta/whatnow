# Evaluation Plan

## Purpose
Defines how WhatNow's AI intake layer and the end-to-end system will be measured,
so "it works" becomes a checkable claim rather than an impression. This plan is
written before the real parser exists (Phase 1) so that Edoardo's evaluation
dataset (E1) and Marta's later testing (M2) are built against the same yardstick.

## Metrics

| Metric | Definition | How it's measured | Owner |
|---|---|---|---|
| Classification accuracy | % of test messages where `case_type` matches the expected label | Compare parser output against Edoardo's labeled evaluation set | Edoardo |
| Field extraction accuracy | % of explicitly-stated fields correctly extracted into `facts` | Compare extracted `facts` against ground-truth annotations per example | Edoardo |
| Valid structured-output rate | % of parser calls that produce schema-valid JSON (no malformed output) | Automated schema validation on parser responses | Edoardo |
| Unsupported-inference rate | % of cases where the parser fills a field with a value not evidenced in the text | Manual + automated check: field present in `facts` but absent from `evidence`/text | Edoardo, verified by Marta |
| Ambiguous-case handling | % of deliberately ambiguous inputs correctly routed to `uncertain_phone_loss` or left with appropriate `missing_fields` rather than forced into a confident wrong answer | Run against ambiguous examples in the evaluation set | Edoardo |
| Prompt-injection resistance | % of adversarial injection attempts that fail to alter system behavior (task status, case type) | Run `evaluations/adversarial_cases.json` injection cases against the live parser + API | Marta |
| Source coverage | % of tasks shown to the user that trace to a recorded, verified source | Cross-check displayed tasks against Gregorio's workflow JSON provenance fields | Gregorio, spot-checked by Marta |
| End-to-end workflow completion | Whether the full flow (message -> facts -> tasks -> completion -> update) succeeds for the canonical MVP scenario in the Master Guide, Section 13 | Manual run-through + any automated integration test | Marta (M3), with Tommaso/Carola |

## What "good enough" means for this MVP

This is a course prototype, not a production system. The evaluation plan's job is
to produce **honest, specific numbers and examples** - not to hit an arbitrary
target score. A documented 70% unsupported-inference-free rate with clear examples
of the failures is more valuable for the course (and for the team) than an
unverified claim of "it works well."

## Relationship to other documents

- Adversarial and ambiguous test inputs used for these metrics live in
  `evaluations/adversarial_cases.json`.
- Pass/fail thresholds a teammate can actually check against are in
  `acceptance_criteria.md`.
- The failure modes these metrics are designed to catch are described in
  `threat_model.md`.

## When this plan is actually run

- **Phase 1 (now):** plan defined, dataset structure agreed with Edoardo,
  adversarial cases authored. No real numbers yet - the parser doesn't exist.
- **Phase 2 (M2, after Edoardo's parser + Tommaso's integration are merged):**
  metrics are run for real against the live system. Results, including
  failures, are recorded in `documentation/failure_mode_results.md` (not
  fabricated in advance).
- **Phase 3 (M3):** end-to-end workflow completion is checked as part of MVP
  acceptance.
