# Prompt benchmark results

Owner: Edoardo Maria Poponcini (Phase E3, branch `test/prompt-benchmark`).

**Status: no real-model run yet.** The evaluator is implemented and tested with fake clients only. Any number that appears in this file before the "Results" section is filled from a real run is invented.

## What is measured

The benchmark sends the same 40 labelled cases (`evaluations/intake_cases.json`, dataset v1) to the model once per prompt version (V1, V2, V3). It then scores each answer against the labels, using the definitions in `documentation/prompt_strategy.md` §4:

| Metric | Section | Headline number |
|---|---|---|
| Valid structured-output rate | 4.3 | valid outputs / N |
| Classification accuracy | 4.1 | correct `case_type` / N (also per class, excluding `label_debatable`, confusion matrix) |
| Field extraction accuracy | 4.2 | correct values / all pairs in `expected_facts` (also per field) |
| Unsupported inference | 4.4 | cases with (a) a filled expected null, (b) bad evidence, or (c) a fact without evidence / N |
| Ambiguous-case handling | 4.5 | lenient pass / 6 uncertain cases (strict and confident-wrong count also reported) |
| Parser-level injection resistance | 4.6 | resisting cases / 5 `prompt_injection` cases |

Additional measurements requested in Tommaso's Phase E3 guidance:

| Measurement | Why |
|---|---|
| `missing_fields` exactly right | Expected value derived as in `evaluations/README.md`: expected nulls in schema order, `[]` for `unsupported` |
| Stolen cases classified `lost_phone` / `uncertain_phone_loss` (with case ids) | V3 is deliberately cautious, and today only `stolen_phone` receives workflow tasks |
| Integration outcome | Each post-parser result goes through the merged `CaseService.create_case_from_intake` and the verified workflow engine, locally with a throwaway in-memory store (no HTTP, no extra model call). For stolen-labelled cases it reports separately those **saved without tasks** (classified lost/uncertain) and those where **intake failed** (no case; the API would answer 502) |
| Out-of-Spain cases (IC-040, Lisbon) | Reports parser result, then integration result, then which Spanish tasks are applied. Observed only; jurisdiction routing is a separate team decision and is not changed here |
| By language | Valid output, classification and field extraction for English (30), Spanish (5), Italian (3) and mixed-language (2) cases. The non-English groups are small, so report counts |
| Parser warnings | Grouped by rule, e.g. how often a fact was nulled for lack of evidence |
| Misclassified cases | Case id, expected, predicted and confidence |

An invalid output fails every metric for its case. It is never removed from the denominator. A provider error (timeout, refusal) is recorded as invalid with the reason `provider_error`.

### Two measurement layers

Each answer is scored twice, from **one** paid call:

- **Raw model output:** strict validation as in §4.3. No cleanup, so a code fence is invalid. This compares the prompts.
- **After parser:** the same answer after `IntakeParser.parse_output()`. The parser strips code fences, sets unquoted facts to `null`, clears `unsupported` cases and recomputes `missing_fields`. This is what the application actually stores.

The two layers must not be mixed. The parser removes grounding violations by construction, so the post-parser unsupported-inference rate shows what the application stores, not how well the prompt behaves.

### What is only partly automated

- Injection resistance criterion 4 (`must_not`): only URLs and a copied `confidence` of 1.0 are checked automatically. Procedures, phone numbers and facts taken from role-play need a manual read of `records.jsonl` for the 5 injection cases.
- String facts are compared after lowercasing, trimming and removing accents. A prediction passes if it contains the expected or an acceptable value.

### Not covered here

- Marta's `evaluations/adversarial_cases.json` uses a different format and a system-level metric (tasks and case type through the API). It stays with her QA work; this benchmark reports only the *parser-level* injection metric.
- `evaluation_plan.md` and `prompt_strategy.md` §5 name `failure_mode_results.md` as the results file. The Phase E3 guide asks for this file and `failures.md`, so parser/prompt results live here, and `failure_mode_results.md` remains Marta's system-level file.

## How to run

From the repository root, with the project venv:

```bash
# 1. Dry run (default): prints the number of calls and a rough cost. No API call.
src/backend/.venv/bin/python -m src.evaluation.run_benchmark

# 2. Mock run: fake client, free, checks the pipeline. Scores are meaningless.
src/backend/.venv/bin/python -m src.evaluation.run_benchmark --mock

# 3. Small real smoke test (6 paid calls), after loading the key into the shell:
set -a; source .env; set +a
src/backend/.venv/bin/python -m src.evaluation.run_benchmark --run --ids IC-001,IC-028

# 4. Full real run (120 paid calls).
src/backend/.venv/bin/python -m src.evaluation.run_benchmark --run

# 5. Re-score a saved run after a metric fix (no API calls).
src/backend/.venv/bin/python -m src.evaluation.run_benchmark --rescore outputs/evaluations/<run folder>
```

Useful options: `--versions v3`, `--limit N`, `--model claude-sonnet-5-5`, and `--raw-delimiters`. The last one does not neutralize fake `<user_message>` tags, which tests the prompt alone as IC-028 was designed to do.

Each run writes a folder `outputs/evaluations/<UTC timestamp>_<model>/` containing:

| File | Content |
|---|---|
| `metadata.json` | model, provider, sampling, max_tokens, SDK version, prompt versions, dataset version, git commit, uncommitted files (excluding `outputs/`), neutralization flag, `mock` flag, and `rescored_utc` if re-scored |
| `records.jsonl` | one line per call: raw model output unmodified, provider error, parser result, parser warnings |
| `metrics.json` | every metric per version and layer, as counts and rates |
| `cases.csv` | one row per case, version and layer: what was right, what was wrong |
| `summary.md` | headline tables |

Real runs are committed as evidence. Mock runs should not be committed.

## Reproducibility and cost

- Default settings: model `claude-haiku-4-5`, provider-default sampling, `max_tokens` 2048, one call per case and version, no retries beyond the SDK's own (2).
- Temperature cannot be set: anthropic SDK 1.x has no sampling parameters (a first real smoke test failed with `TypeError: Messages.create() got an unexpected keyword argument 'temperature'`, before any request was sent). The model's output can therefore vary between runs; compare runs by their `metadata.json` and do not over-read a difference of one or two cases.
- The dry-run cost estimate is rough: about 4 characters per token, 400 output tokens per call, and hard-coded prices. Check the actual cost in the provider console after a run.

## Results

*To be filled from a real run only. Copy the tables from that run's `summary.md` and link the run folder.*

## Representative failures

*To be filled from a real run (hallucinated fact, ambiguous misclassification, injection failure, malformed output). Also recorded in `documentation/failures.md`.*
