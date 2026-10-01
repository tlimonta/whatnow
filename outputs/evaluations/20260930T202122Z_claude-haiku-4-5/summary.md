# Benchmark run 2026-09-30T20:21:22+00:00

Model `claude-haiku-4-5`, sampling provider default (anthropic SDK 1.x accepts no temperature), dataset v1 (40 of 40 cases), commit 2bd15bc (uncommitted: documentation/ai_logs/edoardo.md), delimiter neutralization on.

## v1

| Metric | Raw model output | After parser |
|---|---|---|
| Valid output | 0/40 (0%) | 0/40 (0%) |
| Classification accuracy | 0/40 (0%) | 0/40 (0%) |
| Classification (excl. label_debatable) | 0/37 (0%) | 0/37 (0%) |
| Field extraction accuracy | 0/102 (0%) | 0/102 (0%) |
| missing_fields exactly right | 0/40 (0%) | 0/40 (0%) |
| Stolen cases classified lost/uncertain (lower is better) | 0/19 (0%) | 0/19 (0%) |
| Unsupported inference (case rate, lower is better) | 40/40 (100%) | 40/40 (100%) |
| Unsupported inference (field rate, lower is better) | 0/178 (0%) | 0/178 (0%) |
| Ambiguous handling (lenient) | 0/6 (0%) | 0/6 (0%) |
| Ambiguous handling (strict) | 0/6 (0%) | 0/6 (0%) |
| Uncertain on non-uncertain cases (lower is better) | 0/34 (0%) | 0/34 (0%) |
| Parser-level injection resistance | 0/5 (0%) | 0/5 (0%) |

Invalid reasons (raw): {'code_fence': 40}. Confident-wrong ambiguous cases (raw): 0. Unsupported-inference instances (raw): 0. Unsupported-inference cases that count only because the output is invalid (raw / after parser): 40 / 40.

### By language (after parser)

| Language | Cases | Valid | Classification | Field extraction |
|---|---|---|---|---|
| english | 30 | 0/30 (0%) | 0/30 (0%) | 0/71 (0%) |
| spanish | 5 | 0/5 (0%) | 0/5 (0%) | 0/14 (0%) |
| italian | 3 | 0/3 (0%) | 0/3 (0%) | 0/5 (0%) |
| mixed_language | 2 | 0/2 (0%) | 0/2 (0%) | 0/12 (0%) |

### Integration outcome (merged CaseService + workflow engine, run locally)

- Stolen-labelled cases saved **without tasks**: 0/19 (0%) 
- Stolen-labelled cases where intake failed (no case, API 502): 19/19 (100%) ['IC-001', 'IC-002', 'IC-007', 'IC-008', 'IC-010', 'IC-011', 'IC-012', 'IC-013', 'IC-016', 'IC-017', 'IC-018', 'IC-019', 'IC-027', 'IC-029', 'IC-033', 'IC-034', 'IC-037', 'IC-039', 'IC-040']
- Stolen cases classified lost/uncertain: none
- Workflow errors: 0
- Out of Spain, IC-040 "My phone was stolen in Lisbon yesterday.": case_type `None`, location `None`, tasks None

### Parser warnings

- none

### Misclassified cases (after parser)

- IC-001: expected `stolen_phone`, got `invalid` (confidence None)
- IC-002: expected `stolen_phone`, got `invalid` (confidence None)
- IC-003: expected `lost_phone`, got `invalid` (confidence None)
- IC-004: expected `lost_phone`, got `invalid` (confidence None)
- IC-005: expected `uncertain_phone_loss`, got `invalid` (confidence None)
- IC-006: expected `uncertain_phone_loss`, got `invalid` (confidence None)
- IC-007: expected `stolen_phone`, got `invalid` (confidence None)
- IC-008: expected `stolen_phone`, got `invalid` (confidence None)
- IC-009: expected `lost_phone`, got `invalid` (confidence None)
- IC-010: expected `stolen_phone`, got `invalid` (confidence None)
- IC-011: expected `stolen_phone`, got `invalid` (confidence None)
- IC-012: expected `stolen_phone`, got `invalid` (confidence None)
- IC-013: expected `stolen_phone`, got `invalid` (confidence None)
- IC-014: expected `lost_phone`, got `invalid` (confidence None)
- IC-015: expected `uncertain_phone_loss`, got `invalid` (confidence None)
- IC-016: expected `stolen_phone`, got `invalid` (confidence None)
- IC-017: expected `stolen_phone`, got `invalid` (confidence None)
- IC-018: expected `stolen_phone`, got `invalid` (confidence None)
- IC-019: expected `stolen_phone`, got `invalid` (confidence None)
- IC-020: expected `lost_phone`, got `invalid` (confidence None)
- IC-021: expected `unsupported`, got `invalid` (confidence None)
- IC-022: expected `unsupported`, got `invalid` (confidence None)
- IC-023: expected `unsupported`, got `invalid` (confidence None)
- IC-024: expected `unsupported`, got `invalid` (confidence None)
- IC-025: expected `unsupported`, got `invalid` (confidence None)
- IC-026: expected `unsupported`, got `invalid` (confidence None)
- IC-027: expected `stolen_phone`, got `invalid` (confidence None)
- IC-028: expected `lost_phone`, got `invalid` (confidence None)
- IC-029: expected `stolen_phone`, got `invalid` (confidence None)
- IC-030: expected `unsupported`, got `invalid` (confidence None)
- IC-031: expected `lost_phone`, got `invalid` (confidence None)
- IC-032: expected `uncertain_phone_loss`, got `invalid` (confidence None)
- IC-033: expected `stolen_phone`, got `invalid` (confidence None)
- IC-034: expected `stolen_phone`, got `invalid` (confidence None)
- IC-035: expected `uncertain_phone_loss`, got `invalid` (confidence None)
- IC-036: expected `uncertain_phone_loss`, got `invalid` (confidence None)
- IC-037: expected `stolen_phone`, got `invalid` (confidence None)
- IC-038: expected `lost_phone`, got `invalid` (confidence None)
- IC-039: expected `stolen_phone`, got `invalid` (confidence None)
- IC-040: expected `stolen_phone`, got `invalid` (confidence None)

## v2

| Metric | Raw model output | After parser |
|---|---|---|
| Valid output | 0/40 (0%) | 39/40 (98%) |
| Classification accuracy | 0/40 (0%) | 38/40 (95%) |
| Classification (excl. label_debatable) | 0/37 (0%) | 36/37 (97%) |
| Field extraction accuracy | 0/102 (0%) | 100/102 (98%) |
| missing_fields exactly right | 0/40 (0%) | 28/40 (70%) |
| Stolen cases classified lost/uncertain (lower is better) | 0/19 (0%) | 0/19 (0%) |
| Unsupported inference (case rate, lower is better) | 40/40 (100%) | 12/40 (30%) |
| Unsupported inference (field rate, lower is better) | 0/178 (0%) | 13/178 (7%) |
| Ambiguous handling (lenient) | 0/6 (0%) | 3/6 (50%) |
| Ambiguous handling (strict) | 0/6 (0%) | 3/6 (50%) |
| Uncertain on non-uncertain cases (lower is better) | 0/34 (0%) | 0/34 (0%) |
| Parser-level injection resistance | 0/5 (0%) | 3/5 (60%) |

Invalid reasons (raw): {'code_fence': 40}. Confident-wrong ambiguous cases (raw): 0. Unsupported-inference instances (raw): 0. Unsupported-inference cases that count only because the output is invalid (raw / after parser): 40 / 1.

### By language (after parser)

| Language | Cases | Valid | Classification | Field extraction |
|---|---|---|---|---|
| english | 30 | 29/30 (97%) | 28/30 (93%) | 69/71 (97%) |
| spanish | 5 | 5/5 (100%) | 5/5 (100%) | 14/14 (100%) |
| italian | 3 | 3/3 (100%) | 3/3 (100%) | 5/5 (100%) |
| mixed_language | 2 | 2/2 (100%) | 2/2 (100%) | 12/12 (100%) |

### Integration outcome (merged CaseService + workflow engine, run locally)

- Stolen-labelled cases saved **without tasks**: 0/19 (0%) 
- Stolen-labelled cases where intake failed (no case, API 502): 0/19 (0%) 
- Stolen cases classified lost/uncertain: none
- Workflow errors: 0
- Out of Spain, IC-040 "My phone was stolen in Lisbon yesterday.": case_type `stolen_phone`, location `Lisbon`, tasks ['stolen_phone_es_01']

### Parser warnings

- 39 × removed a Markdown code fence around the JSON

### Misclassified cases (after parser)

- IC-005: expected `uncertain_phone_loss`, got `invalid` (confidence None)
- IC-006: expected `uncertain_phone_loss`, got `lost_phone` (confidence 0.85)

## v3

| Metric | Raw model output | After parser |
|---|---|---|
| Valid output | 0/40 (0%) | 40/40 (100%) |
| Classification accuracy | 0/40 (0%) | 40/40 (100%) |
| Classification (excl. label_debatable) | 0/37 (0%) | 37/37 (100%) |
| Field extraction accuracy | 0/102 (0%) | 101/102 (99%) |
| missing_fields exactly right | 0/40 (0%) | 33/40 (82%) |
| Stolen cases classified lost/uncertain (lower is better) | 0/19 (0%) | 0/19 (0%) |
| Unsupported inference (case rate, lower is better) | 40/40 (100%) | 7/40 (18%) |
| Unsupported inference (field rate, lower is better) | 0/178 (0%) | 8/178 (4%) |
| Ambiguous handling (lenient) | 0/6 (0%) | 6/6 (100%) |
| Ambiguous handling (strict) | 0/6 (0%) | 6/6 (100%) |
| Uncertain on non-uncertain cases (lower is better) | 0/34 (0%) | 0/34 (0%) |
| Parser-level injection resistance | 0/5 (0%) | 4/5 (80%) |

Invalid reasons (raw): {'code_fence': 40}. Confident-wrong ambiguous cases (raw): 0. Unsupported-inference instances (raw): 0. Unsupported-inference cases that count only because the output is invalid (raw / after parser): 40 / 0.

### By language (after parser)

| Language | Cases | Valid | Classification | Field extraction |
|---|---|---|---|---|
| english | 30 | 30/30 (100%) | 30/30 (100%) | 70/71 (99%) |
| spanish | 5 | 5/5 (100%) | 5/5 (100%) | 14/14 (100%) |
| italian | 3 | 3/3 (100%) | 3/3 (100%) | 5/5 (100%) |
| mixed_language | 2 | 2/2 (100%) | 2/2 (100%) | 12/12 (100%) |

### Integration outcome (merged CaseService + workflow engine, run locally)

- Stolen-labelled cases saved **without tasks**: 0/19 (0%) 
- Stolen-labelled cases where intake failed (no case, API 502): 0/19 (0%) 
- Stolen cases classified lost/uncertain: none
- Workflow errors: 0
- Out of Spain, IC-040 "My phone was stolen in Lisbon yesterday.": case_type `stolen_phone`, location `Lisbon`, tasks ['stolen_phone_es_01']

### Parser warnings

- 40 × removed a Markdown code fence around the JSON
- 6 × recomputed missing_fields from the facts
- 1 × dropped evidence for null fact <field>

### Misclassified cases (after parser)

- none

Injection resistance checks `must_not` only for URLs and a copied 1.0 confidence; the other `must_not` items need a manual read of `records.jsonl`.
