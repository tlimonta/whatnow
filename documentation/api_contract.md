# WhatNow core API contract

Owner: Tommaso Limonta. Scope: backend API with single-message AI intake and the
verified stolen-phone Spain workflow.

## Run and test

From the repository root, using the tested Python 3.14.7 environment:

```powershell
python -m venv src/backend/.venv
src/backend/.venv/Scripts/python.exe -m pip install -r requirements.txt
src/backend/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
src/backend/.venv/Scripts/python.exe -m uvicorn src.backend.main:app --host 127.0.0.1 --port 8000
```

The virtual environment is ignored by Git. On macOS/Linux, use
`src/backend/.venv/bin/python` instead of the Windows executable path.
Interactive documentation is at `http://127.0.0.1:8000/docs` and the generated
schema at `/openapi.json`. Use a single server process: restarting (including
development reloads) loses all cases, and separate workers have separate stores.
Dependencies are pinned at the direct-dependency level; the tested transitive
versions are recorded in the AI log. Other Python versions have not been tested.
On this deeply nested Windows checkout, run the SDK tests from a short mapped
drive as described in `documentation/intake_workflow_integration.md`; otherwise
Python may skip the provider-client test module because of path length.

## State and validation

- Case fields: `id`, `case_type`, `status`, `risk_level`, `initial_message`,
  `facts`, `missing_fields`, `tasks`, `created_at`.
- `case_type`: `stolen_phone`, `lost_phone`, `uncertain_phone_loss`,
  `unsupported`, or `null` when not assessed.
- Case `status`: `intake`, `active`, `resolved`.
- `risk_level`: `low`, `medium`, `high`, `critical`, or `null` when not assessed.
- Task fields: `id`, `title`, `status`. Task `status`: `pending`, `completed`,
  `skipped`. Workflow tasks also include `description`, `priority`,
  `workflow_id`, and `source_id`; these optional fields are absent on legacy
  tasks. IDs and titles must contain non-whitespace text.
- `facts` is a JSON object. Successful AI intake populates the seven agreed
  fields: `location`, `incident_time`, `device_type`, `theft_confirmed`,
  `banking_apps_present`, `device_locked`, and `sim_blocked`. Unknown values
  stay `null`. No country is inferred from location text.
- `missing_fields` contains the null fact names for phone cases. The parser
  returns `[]` for `unsupported` cases.
- Generated IDs are UUID4 strings. Lookup paths accept opaque string IDs,
  including future workflow task identifiers; unknown IDs return 404.
- `created_at` is an ISO 8601 timestamp with a timezone, generated in UTC.
- Request fields are case-sensitive. Extra fields are rejected with 422.
- Messages must be strings containing at least one non-whitespace character.
  Accepted text is preserved, including surrounding whitespace.

`case_type: null` remains valid for a case created outside the integrated POST
path or not yet assessed. Successful POST intake returns one of the four case
types. `risk_level` remains null: no verified risk rule exists. Case `status`
remains `intake`: no agreed lifecycle transition rule exists.

## GET /health

Response: **200 OK**

```json
{"status": "ok"}
```

This checks that the application responds; it is not a database or AI health check.

## POST /api/cases

Request:

```json
{"message": "My phone was stolen in Madrid."}
```

Response: **201 Created** (illustrative generated ID and timestamp):

```json
{
  "id": "f8eed2cf-23c6-46af-a7ee-bc30564c162a",
  "case_type": "stolen_phone",
  "status": "intake",
  "risk_level": null,
  "initial_message": "My phone was stolen in Madrid.",
  "facts": {
    "location": "Madrid",
    "incident_time": null,
    "device_type": null,
    "theft_confirmed": true,
    "banking_apps_present": null,
    "device_locked": null,
    "sim_blocked": null
  },
  "missing_fields": ["incident_time", "device_type", "banking_apps_present", "device_locked", "sim_blocked"],
  "tasks": [{
    "id": "stolen_phone_es_01",
    "title": "File a police report (denuncia)",
    "status": "pending",
    "description": "Report the theft to Policía Nacional. If possible, provide identification and a list of the stolen items with the phone's make, model, serial number, and IMEI. Policía Nacional also provides an online reporting route for eligible cases; check the online service's eligibility rules before using it.",
    "priority": "high",
    "workflow_id": "stolen_phone_es",
    "source_id": "policia_nacional_denuncia"
  }],
  "created_at": "2026-09-23T12:00:00Z"
}
```

Every successful request creates a separate case, even for identical messages.
The existing parser classifies the message and extracts
facts; only the deterministic workflow supplies tasks. `stolen_phone` may receive
verified tasks. `lost_phone`, `uncertain_phone_loss`, and `unsupported` receive
no stolen-phone tasks. Clients cannot submit tasks or classified fields.

The parser and provider are created only for a valid POST body. Missing provider
configuration returns **503** `{"detail": "AI intake is not configured"}`.
Provider failure or invalid model output returns **502** with a generic detail.
Workflow loading/evaluation failure returns **503**
`{"detail": "Verified workflow unavailable"}`. These failures do not save a
case. Responses do not include raw model output, credentials, or stack traces.

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

A stolen-phone case can now have verified workflow tasks immediately after POST.
Other case types have no tasks under the current verified data. There is no
public task-creation endpoint.

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

`main.py` validates HTTP input using `schemas.py`, then creates the existing
`IntakeParser` for POST and passes its validated result to `CaseService`.
`CaseService` maps case fields, applies `WorkflowEngine` for stolen-phone cases,
and saves only the final case. `InMemoryCaseStore` saves and returns deep copies.
FastAPI serializes the returned model into JSON. One service and one store belong
to each application instance; a service lock protects concurrent task updates.

Shared models live in `src/models/case.py`. Tests can create an isolated app with
`create_app(intake_parser_factory=...)` and override `get_case_service` with a
service backed by test data. Confidence, evidence, warnings, provider model,
prompt version, and raw model output remain parser-only. Authoritative
procedures, URLs, contacts, and recovery actions come from verified workflow
data. There is no authentication or durable storage.

Implementation references: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
and [Pydantic fields](https://pydantic.dev/docs/validation/latest/concepts/fields/).
