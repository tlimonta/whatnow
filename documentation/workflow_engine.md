# Deterministic workflow engine

## Scope

`src/backend/workflow_engine.py` implements the current stolen-phone workflow for
the Spain MVP. It has no LLM calls and does not read the user's free text. It
accepts an already-structured `Case`, loads the verified workflow and source
catalog, and creates only tasks defined by that workflow.

The engine is intentionally specific to `stolen_phone_es`. It is not a generic
rules language.

## Verified data contract

The workflow file is an object with `workflow_id`, `locale`, `title`,
`description`, and `steps`. Each step contains `id`, `title`, `description`,
`priority`, nullable prose `condition`, and `source_id`.

The source file contains the same `workflow_id` and a `sources` list. Each source
contains `id`, `name`, HTTP(S) `url`, `description`, `type`, and a
`last_verified` date.

Loading validates required fields and types, rejects extra fields, requires
unique step and source IDs, checks that both files name the same workflow, and
checks that every step's `source_id` exists. Invalid JSON, unsupported condition
text, or a missing source reference raises `WorkflowDataError`; the engine does
not continue with partial data.

## Applicability and conditions

The workflow applies only when `case.case_type == "stolen_phone"`. A null,
unsupported, lost-phone, or uncertain case type produces no tasks. The locale is
the current product context: the structured intake schema has no separate
country field, so this phase does not infer a country from `location` text.

Conditions use three results: `true`, `false`, and `unknown`. Only `true`
produces a task. A null or absent fact is `unknown`, never `false`.

Gregorio's workflow stores conditions as human-readable prose rather than a
machine-readable expression. The engine therefore registers the exact supported
step ID and condition text with an explicit evaluator. A changed or new prose
condition fails during loading until code is added deliberately; prose is never
parsed heuristically.

The agreed intake schema currently provides seven facts: `location`,
`incident_time`, `device_type`, `theft_confirmed`, `banking_apps_present`,
`device_locked`, and `sim_blocked`. Their current workflow effects are:

| Workflow condition | Deterministic result |
|---|---|
| `condition: null` (police report) | Always true for an applicable stolen-phone case |
| Banking/payment access | `banking_apps_present: true` is true; `false` is false; null/absent is unknown |
| Carrier is Movistar/Vodafone/Orange/Yoigo | Unknown: carrier is not in the agreed facts |
| Apple device and Buscar enabled | Unknown: Buscar state is not in the agreed facts |
| Android Localizador prerequisites satisfied | Unknown: the prerequisites are not in the agreed facts |
| Manufacturer support/coverage applies | Unknown: coverage eligibility is not in the agreed facts |

A non-boolean, non-null `banking_apps_present` value raises
`WorkflowEvaluationError` instead of being coerced.

## Tasks, traceability, and repeated evaluation

An active workflow step becomes a `Task` using the step's exact `id`, `title`,
`description`, and `priority`. The task also stores the workflow's `workflow_id`
and the step's `source_id`. The source ID is a reference to the validated record
in `data/sources/stolen_phone_es.json`; the engine does not copy or invent URLs,
contacts, or instructions.

The workflow step ID is the task ID. `apply_to_case` upserts by that deterministic
ID, so running it repeatedly does not make duplicates. When the same workflow
task already exists, its content is refreshed from verified data while its
`pending`, `completed`, or `skipped` status is preserved. Existing unrelated
tasks are preserved. Reusing a workflow step ID for an unrelated task, or a case
that already contains duplicate task IDs, fails clearly.

Recalculation also reconciles tasks that are no longer applicable. A `pending`
task from this workflow is removed when its condition becomes false or unknown,
or when the case is no longer a stolen-phone case. A `completed` or `skipped`
task is retained as historical state. Tasks from another workflow and unrelated
legacy tasks are never removed or modified.

## Usage

```python
from src.backend.workflow_engine import WorkflowEngine

engine = WorkflowEngine.from_files()
updated_case = engine.apply_to_case(case)
```

The POST intake path now calls this method through `CaseService` after the parser
returns validated structured facts for a stolen-phone case. The service saves
the resulting case only after workflow evaluation succeeds. Other case types
do not invoke the stolen-phone workflow.

## Current limitations

- Only stolen-phone cases in the Spain MVP are supported.
- Most conditional steps remain unknown because the agreed facts do not contain
  carrier, Buscar, Localizador prerequisite, or coverage information.
- Prose conditions require a matching explicit evaluator in code; there is no
  general expression language.
- The source catalog is validated and referenced by ID, but there is no separate
  source API or frontend integration in this phase.
- The engine does not classify text, extract facts, calculate risk, call external
  services, or re-verify source freshness.
- The in-memory store and its restart/process limitations are unchanged.
