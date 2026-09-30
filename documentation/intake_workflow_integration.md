# Single-message intake and workflow integration

`POST /api/cases` validates the `message` body, then constructs the existing
`IntakeParser` with `AnthropicClient`. Parser construction is lazy: importing the
app, checking `/health`, or sending an invalid POST body does not contact the
provider or require its key. The parser sends one prompt, validates the model
output, and applies its evidence and null rules.

`ANTHROPIC_API_KEY` is required for live intake. `ANTHROPIC_WORKSPACE_ID` is
optional: leave it unset for a workspace-scoped key, or set it when Anthropic
requires the `anthropic-workspace-id` header. The provider client configures
that header once during construction and does not expose either value in API
errors.

The route passes only `ParsedIntake.result` into `CaseService`. The service copies
`case_type`, all seven typed `facts`, and `missing_fields` into `Case`, retaining
the original `initial_message`. It does not persist confidence, evidence,
warnings, prompt version, provider model, or raw model output. No parser text
becomes a task or procedure.

For `stolen_phone`, the service loads and applies `WorkflowEngine`. The engine
validates the workflow and source files, checks conditions against known facts,
and creates tasks exclusively from verified steps, with `workflow_id` and
`source_id` traceability. Unknown facts remain null; a conditional task appears
only when its condition is definitively true. The service saves the case after
both parsing and workflow evaluation succeed. The engine's established
reconciliation rules still govern any later explicit application.

`lost_phone`, `uncertain_phone_loss`, and `unsupported` are stored with their
validated classification and facts but receive no stolen-phone workflow tasks.
The parser schema requires one of those four classifications, so a null or
invalid model classification fails intake rather than being guessed. No verified
lost-phone or uncertain-phone workflow exists yet.

The current workflow data has no risk calculation rule, and the project has no
agreed transition from `intake` to `active`. Accordingly, successful cases keep
`risk_level: null` and `status: intake`. The parser's `location` is free text;
it does not establish an independently verified country. The workflow is scoped
to the Spain MVP, and out-of-Spain routing needs a later team decision.

## Failures

| Failure | HTTP response | Case saved? |
|---|---|---|
| Invalid request body | 422 validation error | No |
| Missing provider key or SDK | 503 `AI intake is not configured` | No |
| Provider failure | 502 `AI provider request failed` | No |
| Invalid model output | 502 `AI intake response was invalid` | No |
| Invalid or unavailable verified workflow | 503 `Verified workflow unavailable` | No |

The API returns fixed error messages rather than provider exception text, raw
model output, or stack traces. Unit and integration tests supply fake clients;
they make no external AI request. The API remains single-message only, with
process-local storage and no conversational updates, database, or frontend
integration in this phase.

On Windows, this repository's deeply nested path can exceed the SDK's supported
path length for one imported module. The current checkout was tested successfully
through a temporary `subst W: <repository path>` mapping. Start Python from that
short path for full SDK tests or local provider use; remove the mapping with
`subst W: /D` when finished. The API returns its safe configuration error if an
Anthropic module cannot be imported from the long path.
