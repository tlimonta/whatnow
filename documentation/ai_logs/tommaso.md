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
