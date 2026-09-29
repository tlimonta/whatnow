# Tommaso Limonta: AI assistance and evaluation log

## Session: 2026-09-23

Project: WhatNow, DAT32-91 Prompt Engineering and Git.
Branch inspected: `feature/core-case-engine`.
Assistant: OpenAI Codex. Human owner: Tommaso Limonta.

### Prompt and constraints

Tommaso asked Codex to implement the core backend architecture, shared case/task
models, in-memory storage, service layer, initial FastAPI routes, tests, and
documentation. The prompt required repository inspection before editing, a plan
before implementation, minimal dependencies, and no Git branch changes, commits,
or pushes. Changes were limited to the assigned backend/model/test/documentation
paths and `requirements.txt`.

The critical constraint was that the LLM must not invent official procedures,
contact details, URLs, or recovery actions. There is no AI integration in this
branch. New cases remain in intake with unknown classification and risk.

### Prompt evolution and decisions

Only one user implementation prompt had been received at implementation time;
no additional user prompt iterations or corrections are claimed here.
Codex inspected the scaffold and proposed the API -> service -> store flow.
Implementation decisions were to use nullable classification/risk rather than
fake inference, preserve original message text, validate enum values, isolate
storage per app, return copies of nested state, and serialize service updates.
The task PATCH route returns the updated full case. Workflow/source metadata
remains a later team integration decision.

### What Codex assisted with

Codex drafted the Python implementation, automated tests, API contract, storage
decision, and this log. It installed dependencies in the ignored local virtual
environment, ran the test suite, and reviewed the changes against the requested
scope. Official FastAPI testing and Pydantic field documentation were consulted;
no life-admin procedures or advice were researched or generated.

### Systematic evaluation

Environment: Windows PowerShell, Python 3.14.7.
Direct dependencies: FastAPI 0.141.1, Pydantic 2.13.5, Uvicorn 0.53.0,
pytest 9.1.1, HTTPX 0.28.1.

Resolved transitive versions from `pip freeze` for reproduction reference:

```text
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.15.1
certifi==2026.7.22
click==8.5.0
colorama==0.4.6
h11==0.16.0
httpcore==1.0.9
idna==3.20
iniconfig==2.3.0
packaging==26.3
pluggy==1.6.0
pydantic_core==2.46.5
Pygments==2.21.0
starlette==1.7.0
typing-inspection==0.4.4
typing_extensions==4.16.0
```

Command from the repository root:

```powershell
src/backend/.venv/Scripts/python.exe -m pytest tests/backend -q -p no:cacheprovider
```

Coverage of behavior:

- Health response and creation/retrieval round trip.
- Unique IDs, UTC timestamps, original-message preservation, and neutral intake.
- Lost-phone, stolen-phone, and unrelated messages produce no inferred facts,
  classification, risk level, or tasks.
- Unknown case/task errors, including a task belonging to a different case.
- All allowed enum values; rejection of invalid values, null required fields,
  blank text, naive timestamps, and extra request fields.
- Task completion, repeated completion, skipping, reopening, and persistence.
- Invalid task updates leave stored data unchanged.
- Concurrent updates to distinct tasks preserve every completed task.
- Copies isolate nested state, mutable defaults are independent, and app/store
  instances do not share cases.

Initial run: **52 passed** with no failing tests and two warnings.
Final run with the command above: **52 passed in 0.30 seconds**, with only the
Starlette HTTPX deprecation warning remaining. `pip check` reported no broken
requirements. A separate live Uvicorn process passed HTTP smoke checks for health,
case creation, case retrieval, and OpenAPI schema availability, then was stopped.

### Observed issues and limitations

1. The first test run could not create pytest's optional cache in the repository
   root (Windows access-denied warning). Reproduction commands disable the cache
   plugin; caching is not needed for correctness.
2. Starlette 1.7.0 reports that using HTTPX with its TestClient is deprecated in
   favor of HTTPX2. All tests pass with the pinned HTTPX dependency. This warning
   is left visible; a later dependency update should review the supported test
   client. No extra dependency was added just to suppress the warning.
3. No AI accuracy or prompt-classification evaluation was performed: no AI is
   connected. Likewise, no official workflow correctness is claimed.
4. Storage is temporary and process-local. Direct dependencies are pinned; this
   branch does not introduce a full transitive lockfile.

### Manual review and attribution

**Human manual code review: pending Tommaso's review.** Codex cannot attest that
Tommaso has reviewed or personally run the code. Automated tests were run by
Codex; they do not substitute for human review.

Before committing, Tommaso should inspect the diff, run the documented command,
and confirm the nullable intake fields, task response contract, storage lifetime,
and lack of AI/procedure generation. After actually completing those steps, add
the review date, test result, and any corrections here. Suggested wording to use
only after completion: "Codex assisted with implementation; I manually reviewed
the code and ran the tests."

No branch was created/switched, and no commit or push was performed by Codex.

## Human verification

I manually reviewed the backend structure and the changes created with Codex.

I ran the complete automated test suite locally:

- 52 tests passed
- 1 dependency deprecation warning remained

I also ran the FastAPI application locally and manually tested the API
through Swagger.

Verified endpoints included:

- GET /health
- POST /api/cases
- GET /api/cases/{case_id}
- handling of unknown case IDs
- task update error handling where applicable

I confirmed that new cases remain in the intake state and that the backend
does not perform AI classification or invent case facts.

I also reviewed the Git diff before committing the work.

## Session: 2026-09-29

Project: WhatNow, DAT32-91 Prompt Engineering and Git.
Branch inspected: `feature/workflow-engine`.
Assistant: OpenAI Codex. Human owner: Tommaso Limonta.

### Request and inspection

Tommaso asked Codex to implement the deterministic workflow engine for the
stolen-phone Spain MVP without changing branches, committing, pushing, merging,
or modifying Gregorio's verified data. Before editing, Codex inspected the
backend models, API, service, storage, backend tests, both verified JSON files,
the API contract, architecture/decision documents, research notes, threat model,
prompt strategy, evaluation schema, and the existing AI log. The working tree
was clean and the requested branch was already active.

The real workflow contains nine steps. Conditions are nullable prose strings,
not machine-readable expressions. The source catalog contains nine records. The
repository's agreed intake schema has seven facts, but it has no carrier,
Buscar/Localizador prerequisite, or coverage fields. Codex therefore did not
invent those values or rewrite the data: unsupported conditions remain unknown.
Only the unconditional police step and the banking condition can currently be
resolved from the agreed facts.

### AI-assisted implementation

Codex drafted `src/backend/workflow_engine.py`, extended `Task` with optional
workflow-backed description, priority, workflow ID, and source ID fields, and
added focused backend tests. The engine strictly validates the real workflow
and source structures, source references, workflow ID alignment, and supported
condition text. It uses tri-state evaluation, deterministic step IDs for task
identity, and idempotent task upserts that preserve existing status.

Codex also drafted `documentation/workflow_engine.md` and this session record.
No AI parser, LLM call, frontend integration, database, external API, web
scraping, or dependency was added. The verified workflow and source JSON files
were not modified.

### Automated evaluation performed by Codex

Command run from the repository root with the existing ignored virtual
environment:

```powershell
src/backend/.venv/Scripts/python.exe -m pytest tests/backend -q -p no:cacheprovider
```

The first full backend run after implementation completed with **72 passed in
0.48 seconds** and one existing Starlette TestClient deprecation warning about
HTTPX. After adding two malformed-data checks and a legacy serialization check,
the final backend run completed with **75 passed in 0.32 seconds** and the same
warning. `pip check` reported no broken requirements, and `git diff --check`
found no whitespace errors. Codex also reviewed the final diff and status; exact
changed files and status are reported in the assistant's final response for this
session.

### Human review status

**Human review of this workflow-engine change is pending.** This entry does not
claim that Tommaso reviewed the code, validated Gregorio's source content, or ran
the tests himself. Codex did not create or switch a branch and did not commit,
push, or merge. Tommaso should inspect the condition-to-fact interpretation,
provenance fields, status-aware reconciliation policy, diff, and test output before
committing.

### Targeted reconciliation refinement

After review feedback, Codex changed only workflow task reconciliation and its
tests/documentation. Pending tasks produced by `stolen_phone_es` are now removed
when they are no longer definitively applicable or the case type changes.
Completed and skipped tasks remain as history, while unrelated tasks and tasks
from other workflows are left untouched. Duplicate and ID-collision checks are
unchanged. The first refinement run completed with **82 passed in 0.32 seconds**;
after adding explicit historical-state coverage for null and unsupported case
types, the final run completed with **86 passed in 0.34 seconds**. Both runs had
the existing Starlette TestClient deprecation warning, and the final
`git diff --check` completed without errors. No human verification of this
refinement is claimed here.
