# Intake Prompt V1: Initial (naive) attempt

| | |
|---|---|
| Version | V1 |
| Date | 2026-09-28 |
| Author | Edoardo Maria Poponcini (drafted with Claude Code) |
| Issue | AI-01 |
| Purpose | First, minimal attempt at turning a user's free-text description of a lost or stolen phone into structured data. It is a deliberately simple baseline for V2 and V3 to be compared against. |
| Status | Not yet run against any model. No results exist. |

## Prompt

`{user_message}` is replaced with the raw user text at run time.

```text
You are a helpful assistant for an app that helps people who lost their phone or had it stolen.

Read the user's message and tell me what happened. Classify the case as stolen, lost or something else, and extract the important details like where it happened, when, what phone it is, if they have banking apps, if the phone is locked and if the SIM is blocked.

Answer in JSON.

User message: {user_message}
```

## Design intent

This is the prompt a first-time author would realistically write: it names the task and the details we care about, and it asks for JSON. It does not attempt to be robust.

## Known weaknesses / expected failures

- **Loose output format.** "Answer in JSON" does not fix key names, nesting or types. Expect keys like `status`, `details`, `where`, `phone_model`, and Markdown code fences or a prose sentence around the JSON. This should lower the **valid structured-output rate**.
- **Labels do not match the backend enum.** "stolen, lost or something else" will produce values like `"stolen"`, `"lost"` or `"other"` instead of `stolen_phone` / `lost_phone` / `unsupported`.
- **No uncertain category.** There is no `uncertain_phone_loss`, so ambiguous messages (IC-005, IC-015, IC-032) are forced into stolen or lost. Expect poor **ambiguous-case handling**.
- **No null rules.** Nothing says what to do with unknown information. Expect guessed values (for example `banking_apps_present: true` because "most people have one", or a city inferred from "the metro"), empty strings, `"unknown"`, or omitted keys. This should raise the **unsupported inference rate**.
- **No null vs false distinction.** Expect "not mentioned" and "explicitly denied" to be confused.
- **No evidence or confidence.** Outputs cannot be checked against the source text.
- **No instruction/data separation.** The user text is appended directly after the instructions, so "Ignore all previous rules..." (IC-027, IC-029) has the same standing as the system text. Expect weak **parser-level prompt-injection resistance**.
- **"Helpful assistant" + "tell me what happened"** invites advice. Expect the model to add recovery steps, police or carrier phone numbers, or URLs, which violates the architecture rule that procedures come only from verified workflow data.
- **No handling of unsupported or irrelevant input.** A weather question (IC-024) may still get a phone-shaped JSON object.
