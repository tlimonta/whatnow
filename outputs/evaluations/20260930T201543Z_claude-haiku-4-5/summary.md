# Benchmark run 2026-09-30T20:15:43+00:00

Model `claude-haiku-4-5`, sampling provider default (anthropic SDK 1.x accepts no temperature), dataset v1 (2 of 40 cases), commit a5e807e (uncommitted: (not recorded)), delimiter neutralization on.

## v1

| Metric | Raw model output | After parser |
|---|---|---|
| Valid output | 0/2 (0%) | 0/2 (0%) |
| Classification accuracy | 0/2 (0%) | 0/2 (0%) |
| Classification (excl. label_debatable) | 0/2 (0%) | 0/2 (0%) |
| Field extraction accuracy | 0/8 (0%) | 0/8 (0%) |
| missing_fields exactly right | 0/2 (0%) | 0/2 (0%) |
| Stolen cases classified lost/uncertain (lower is better) | 0/2 (0%) | 0/2 (0%) |
| Unsupported inference (case rate, lower is better) | 2/2 (100%) | 2/2 (100%) |
| Unsupported inference (field rate, lower is better) | 0/6 (0%) | 0/6 (0%) |
| Ambiguous handling (lenient) | n/a | n/a |
| Ambiguous handling (strict) | n/a | n/a |
| Uncertain on non-uncertain cases (lower is better) | 0/2 (0%) | 0/2 (0%) |
| Parser-level injection resistance | n/a | n/a |

Invalid reasons (raw): {'code_fence': 2}. Confident-wrong ambiguous cases (raw): 0. Unsupported-inference instances (raw): 0. Unsupported-inference cases that count only because the output is invalid (raw / after parser): 2 / 2.

### By language (after parser)

| Language | Cases | Valid | Classification | Field extraction |
|---|---|---|---|---|
| english | 2 | 0/2 (0%) | 0/2 (0%) | 0/8 (0%) |

### Integration outcome (merged CaseService + workflow engine, run locally)

- Stolen-labelled cases saved **without tasks**: 0/2 (0%) 
- Stolen-labelled cases where intake failed (no case, API 502): 2/2 (100%) ['IC-001', 'IC-040']
- Stolen cases classified lost/uncertain: none
- Workflow errors: 0
- Out of Spain, IC-040 "My phone was stolen in Lisbon yesterday.": case_type `None`, location `None`, tasks None

### Parser warnings

- none

### Misclassified cases (after parser)

- IC-001: expected `stolen_phone`, got `invalid` (confidence None)
- IC-040: expected `stolen_phone`, got `invalid` (confidence None)

## v2

| Metric | Raw model output | After parser |
|---|---|---|
| Valid output | 0/2 (0%) | 2/2 (100%) |
| Classification accuracy | 0/2 (0%) | 2/2 (100%) |
| Classification (excl. label_debatable) | 0/2 (0%) | 2/2 (100%) |
| Field extraction accuracy | 0/8 (0%) | 8/8 (100%) |
| missing_fields exactly right | 0/2 (0%) | 2/2 (100%) |
| Stolen cases classified lost/uncertain (lower is better) | 0/2 (0%) | 0/2 (0%) |
| Unsupported inference (case rate, lower is better) | 2/2 (100%) | 0/2 (0%) |
| Unsupported inference (field rate, lower is better) | 0/6 (0%) | 0/6 (0%) |
| Ambiguous handling (lenient) | n/a | n/a |
| Ambiguous handling (strict) | n/a | n/a |
| Uncertain on non-uncertain cases (lower is better) | 0/2 (0%) | 0/2 (0%) |
| Parser-level injection resistance | n/a | n/a |

Invalid reasons (raw): {'code_fence': 2}. Confident-wrong ambiguous cases (raw): 0. Unsupported-inference instances (raw): 0. Unsupported-inference cases that count only because the output is invalid (raw / after parser): 2 / 0.

### By language (after parser)

| Language | Cases | Valid | Classification | Field extraction |
|---|---|---|---|---|
| english | 2 | 2/2 (100%) | 2/2 (100%) | 8/8 (100%) |

### Integration outcome (merged CaseService + workflow engine, run locally)

- Stolen-labelled cases saved **without tasks**: 0/2 (0%) 
- Stolen-labelled cases where intake failed (no case, API 502): 0/2 (0%) 
- Stolen cases classified lost/uncertain: none
- Workflow errors: 0
- Out of Spain, IC-040 "My phone was stolen in Lisbon yesterday.": case_type `stolen_phone`, location `Lisbon`, tasks ['stolen_phone_es_01']

### Parser warnings

- 2 × removed a Markdown code fence around the JSON

### Misclassified cases (after parser)

- none

## v3

| Metric | Raw model output | After parser |
|---|---|---|
| Valid output | 0/2 (0%) | 2/2 (100%) |
| Classification accuracy | 0/2 (0%) | 2/2 (100%) |
| Classification (excl. label_debatable) | 0/2 (0%) | 2/2 (100%) |
| Field extraction accuracy | 0/8 (0%) | 8/8 (100%) |
| missing_fields exactly right | 0/2 (0%) | 2/2 (100%) |
| Stolen cases classified lost/uncertain (lower is better) | 0/2 (0%) | 0/2 (0%) |
| Unsupported inference (case rate, lower is better) | 2/2 (100%) | 0/2 (0%) |
| Unsupported inference (field rate, lower is better) | 0/6 (0%) | 0/6 (0%) |
| Ambiguous handling (lenient) | n/a | n/a |
| Ambiguous handling (strict) | n/a | n/a |
| Uncertain on non-uncertain cases (lower is better) | 0/2 (0%) | 0/2 (0%) |
| Parser-level injection resistance | n/a | n/a |

Invalid reasons (raw): {'code_fence': 2}. Confident-wrong ambiguous cases (raw): 0. Unsupported-inference instances (raw): 0. Unsupported-inference cases that count only because the output is invalid (raw / after parser): 2 / 0.

### By language (after parser)

| Language | Cases | Valid | Classification | Field extraction |
|---|---|---|---|---|
| english | 2 | 2/2 (100%) | 2/2 (100%) | 8/8 (100%) |

### Integration outcome (merged CaseService + workflow engine, run locally)

- Stolen-labelled cases saved **without tasks**: 0/2 (0%) 
- Stolen-labelled cases where intake failed (no case, API 502): 0/2 (0%) 
- Stolen cases classified lost/uncertain: none
- Workflow errors: 0
- Out of Spain, IC-040 "My phone was stolen in Lisbon yesterday.": case_type `stolen_phone`, location `Lisbon`, tasks ['stolen_phone_es_01']

### Parser warnings

- 2 × removed a Markdown code fence around the JSON

### Misclassified cases (after parser)

- none

Injection resistance checks `must_not` only for URLs and a copied 1.0 confidence; the other `must_not` items need a manual read of `records.jsonl`.
