# WhatNow core API contract

Owner: Tommaso Limonta. Scope: initial backend, without AI or workflow integration.

## Run and test

From the repository root, using the tested Python 3.14.7 environment:

```powershell
python -m venv src/backend/.venv
src/backend/.venv/Scripts/python.exe -m pip install -r requirements.txt
src/backend/.venv/Scripts/python.exe -m pytest tests/backend -q -p no:cacheprovider
src/backend/.venv/Scripts/python.exe -m uvicorn src.backend.main:app --host 127.0.0.1 --port 8000
```

The virtual environment is ignored by Git. On macOS/Linux, use
`src/backend/.venv/bin/python` instead of the Windows executable path.
Interactive documentation is at `http://127.0.0.1:8000/docs` and the generated
schema at `/openapi.json`. Use a single server process: restarting (including
development reloads) loses all cases, and separate workers have separate stores.
Dependencies are pinned at the direct-dependency level; the tested transitive
versions are recorded in the AI log. Other Python versions have not been tested.

## State and validation

- Case fields: `id`, `case_type`, `status`, `risk_level`, `initial_message`,
  `facts`, `missing_fields`, `tasks`, `created_at`.
- `case_type`: `stolen_phone`, `lost_phone`, `uncertain_phone_loss`,
  `unsupported`, or `null` when not assessed.
- Case `status`: `intake`, `active`, `resolved`.
- `risk_level`: `low`, `medium`, `high`, `critical`, or `null` when not assessed.
- Task fields: `id`, `title`, `status`. Task `status`: `pending`, `completed`,
  `skipped`. IDs and titles must contain non-whitespace text.
- `facts` is a JSON object. Unknown values stay `null`; absent keys mean that
  fact has not been collected. No country or other fact is inferred here.
- `missing_fields` is a list of field names. Its initial empty value means
  missing information has not been assessed, not that intake is complete.
- Generated IDs are UUID4 strings. Lookup paths accept opaque string IDs,
  including future workflow task identifiers; unknown IDs return 404.
- `created_at` is an ISO 8601 timestamp with a timezone, generated in UTC.
- Request fields are case-sensitive. Extra fields are rejected with 422.
- Messages must be strings containing at least one non-whitespace character.
  Accepted text is preserved, including surrounding whitespace.

Intake uses `case_type: null` rather than `unsupported`: the application has
not yet determined whether the user's situation is supported. `unsupported`
is reserved for a later explicit classification. Risk also remains unknown.

## GET /health

Response: **200 OK**

```json
{"status": "ok"}
```

This checks that the application responds; it is not a database or AI health check.

## POST /api/cases

Request:

```json
{"message": "I cannot find my phone in Madrid."}
```

Response: **201 Created** (illustrative generated ID and timestamp):

```json
{
  "id": "f8eed2cf-23c6-46af-a7ee-bc30564c162a",
  "case_type": null,
  "status": "intake",
  "risk_level": null,
  "initial_message": "I cannot find my phone in Madrid.",
  "facts": {},
  "missing_fields": [],
  "tasks": [],
  "created_at": "2026-09-23T12:00:00Z"
}
```

Every successful request creates a separate case, even for identical messages.
There is no classification, fact extraction, risk assessment, or workflow
generation in this branch. Clients cannot submit tasks or classified fields.

## GET /api/cases/{case_id}

Response: **200 OK**, with the full case object shown above and current task state.
Unknown case: **404 Not Found**:

```json
{"detail": "Case not found"}
```

## PATCH /api/cases/{case_id}/tasks/{task_id}

Request:

```json
{"status": "completed"}
```

Response: **200 OK**, containing the entire updated case. For a future case
with a task, its `tasks` list would contain an object such as:

```json
[{"id": "example-step", "title": "Example task for testing only", "status": "completed"}]
```

Any of the three task statuses may replace the current one, allowing completion,
skipping, and reopening. Repeating the same update succeeds without additional
effects. Only the matching task within the specified case changes. Updating tasks
does not automatically change case status or resolve a case.

Unknown case: **404**, `{"detail": "Case not found"}`.
Existing case without that task: **404**, `{"detail": "Task not found"}`.

New cases currently have no tasks, so PATCH against a newly created case returns
the task 404. Successful updates are exercised with test-only seeded tasks;
there is no public task-creation endpoint. Task titles and later source metadata
must come from verified workflow data when that integration is implemented.
The minimal task model does not yet define the workflow/source schema.

## Invalid requests

Malformed JSON, missing required fields, blank messages, incorrect types, invalid
statuses, and unexpected fields return **422 Unprocessable Entity** with FastAPI's
validation error list. For example, posting `{}` returns:

```json
{
  "detail": [
    {"type": "missing", "loc": ["body", "message"], "msg": "Field required", "input": {}}
  ]
}
```

Clients should rely on the status and error locations, not exact validation
wording. Request validation happens before case lookup, so an invalid PATCH body
returns 422 even if the case ID is unknown.

## Architecture and integration boundary

`main.py` validates HTTP input using `schemas.py`, calls `CaseService`, and maps
domain not-found errors to HTTP 404. `CaseService` creates intake cases or updates
task state, while `InMemoryCaseStore` saves and returns deep copies of `Case`.
FastAPI serializes the returned model into JSON. One service and one store belong
to each application instance; a service lock protects concurrent task updates.

Shared models live in `src/models/case.py`. Tests can create an isolated app with
`create_app()` and override `get_case_service` with a service backed by test data.
Future AI code may propose classifications and facts; authoritative procedures,
URLs, contacts, and recovery actions must come from verified deterministic data.
This branch has no AI calls, official advice, authentication, or durable storage.

Implementation references: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
and [Pydantic fields](https://pydantic.dev/docs/validation/latest/concepts/fields/).
