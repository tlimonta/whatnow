# Intake Prompt V2: Structured output

| | |
|---|---|
| Version | V2 |
| Date | 2026-09-28 |
| Author | Edoardo Maria Poponcini (drafted with Claude Code) |
| Issue | AI-01 |
| Purpose | Make the output machine-checkable. Fix the allowed categories to the backend `CaseType` enum, give an explicit JSON schema, define null handling, and require JSON-only output. |
| Status | Not yet run against any model. No results exist. |

## Changes from V1

1. Role narrowed from "helpful assistant" to "information extraction component", with an explicit ban on advice, procedures and contact details.
2. The four allowed `case_type` values are listed verbatim, each with a one-line definition.
3. An explicit JSON schema is given, with fixed key names and types for all seven facts.
4. Null rules: unknown means `null`, and `false` only when the user explicitly says so.
5. `missing_fields` and a basic `evidence` list are defined.
6. Output constraint: a single JSON object, no Markdown fences, no extra text.

## Prompt

`{user_message}` is replaced with the raw user text at run time.

```text
You are the information extraction component of WhatNow, an app that helps people in Spain whose mobile phone has been lost or stolen.

Your only job is to read the user's message and return structured facts about the incident. You do not give advice. Do not write procedures, recovery steps, tasks, phone numbers, URLs or legal information.

ALLOWED CASE TYPES (use exactly one of these strings):
- "stolen_phone": the user says their phone was stolen.
- "lost_phone": the user says they lost their phone.
- "uncertain_phone_loss": the phone is missing but it is not clear whether it was lost or stolen.
- "unsupported": the message is not about a lost or stolen phone.

OUTPUT SCHEMA:
{
  "case_type": "stolen_phone" | "lost_phone" | "uncertain_phone_loss" | "unsupported",
  "confidence": number between 0.0 and 1.0,
  "facts": {
    "location": string or null,
    "incident_time": string or null,
    "device_type": string or null,
    "theft_confirmed": true, false or null,
    "banking_apps_present": true, false or null,
    "device_locked": true, false or null,
    "sim_blocked": true, false or null
  },
  "missing_fields": [list of fact names whose value is null],
  "evidence": [{"field": fact name, "user_text": text from the message}]
}

FIELD MEANINGS:
- location: where the incident happened.
- incident_time: when the incident happened, as the user described it.
- device_type: the phone brand, model or operating system, in lowercase (for example "iphone", "samsung", "android").
- theft_confirmed: whether the user says the phone was stolen.
- banking_apps_present: whether banking or payment apps are on the phone.
- device_locked: whether the phone has a screen lock (PIN, password, Face ID, fingerprint).
- sim_blocked: whether the user has already blocked the SIM card.

RULES:
1. If the message does not state a fact, set it to null. Do not guess.
2. Use false only when the user explicitly says the opposite (for example "I don't have banking apps").
3. Always include all seven keys in "facts".
4. "missing_fields" lists the names of the facts that are null.
5. For each fact that is not null, add one "evidence" item quoting the part of the message that supports it.
6. Respond with the JSON object only. No Markdown, no code fences, no explanation before or after.

User message:
{user_message}
```

## Known weaknesses / expected failures

- **Thin definition of uncertainty.** `uncertain_phone_loss` is defined in one line, with no rules for hedged theft ("maybe someone took it"), retracted claims (IC-015), or disappearance with no stated cause (IC-006). Expect V2 still to pick stolen or lost on ambiguous inputs, driven by the first verb it sees.
- **Hedged facts.** Rule 1 says "do not guess" but does not say that the *user's* guesses ("I guess around midnight", IC-034) are not facts. Expect guessed times and places to be extracted.
- **No injection defence.** The user message is still appended after a plain label with no delimiters and no statement that it is data. Instruction-like text (IC-027, IC-029, IC-031) and fake role text (IC-030) may still be obeyed.
- **Evidence is not grounded.** "Quoting the part of the message" does not require an exact substring. Expect paraphrased or translated evidence, and evidence for facts the model inferred.
- **Confidence is undefined.** "Number between 0.0 and 1.0" gives no meaning or calibration guidance. Expect values clustered near 0.9-1.0 regardless of ambiguity.
- **Unsupported scope is vague.** "Not about a lost or stolen phone" leaves open hypotheticals (IC-026), phones still in the user's hand (IC-022) and non-phone thefts (IC-023), and does not say that facts should be null for unsupported cases (IC-021 may extract "Madrid").
- **`missing_fields` for unsupported cases.** Rule 4 lists every null fact, so for an `unsupported` message V2 should output all 7 names, while the dataset expects `[]` (a rule added in V3). This is a definitional difference by design, not a model error.
- **Value formats only partly defined.** Location and time may be translated or normalised inconsistently.
- **Longer than V1.** It adds tokens and latency, but it is still far shorter than V3.
