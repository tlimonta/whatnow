# Privacy and Ethics

## Purpose of this document
This document defines what personal data WhatNow needs, what it must never request,
how that data should be minimized and retained, and the ethical risks the team must
design against. It distinguishes verified legal principles from the team's own
product recommendations, and it is not legal advice.

## 1. Data inventory

WhatNow's `Case` model stores: a freeform `initial_message` (the user's own words,
verbatim and unedited), a `facts` dictionary populated by the AI intake parser, a
`missing_fields` list, and a list of `tasks`. There is no user account, login, or
persistent identifier linking a case to a real-world identity.

| Data | Why it's needed | Sensitivity | Minimization note |
|---|---|---|---|
| `initial_message` (raw text) | Source for AI extraction; useful for debugging/audit | Moderate-high: user-authored free text can contain anything, including data we never asked for | Should be treated as the highest-sensitivity field in the system, not a routine log |
| `location` | Determines which country/region's procedures apply | Low-moderate | City-level is sufficient; do not request precise coordinates |
| `incident_time` | Some actions are time-sensitive (e.g. bank notification windows) | Low | |
| `device_type` | Recovery steps differ (iOS vs Android) | Low | |
| `theft_confirmed` | Routes stolen vs. lost workflow | Low | |
| `banking_apps_present` | Flags financial-fraud urgency tasks | Moderate - reveals a fact about the user's financial life | Store as boolean/null, never account details |
| `device_locked`, `sim_blocked` | Tracks which protective steps are already done | Low | |

**Design strength worth documenting:** because there is no account system, a case
cannot be linked back to a specific person by the application itself - only by
whatever identifying detail the user chooses to type into `initial_message`. This
is a meaningful minimization property, and the team should avoid undermining it by
later adding logins, IP logging tied to cases, or analytics identifiers without a
documented reason.

## 2. Data the app must never request

Per team policy, the application and any prompts must actively discourage the user
from providing, and must never store as a normal case fact:

- Passwords
- PINs
- Authentication / verification codes (SMS codes, 2FA codes)
- Full payment card numbers or CVV
- Banking login credentials
- Device or account recovery secrets (recovery keys, security-question answers)

**Known gap (flagged, not yet solved):** the `facts` field is an open dictionary
(`dict[str, JsonValue]`), and `initial_message` is stored in full. Nothing at the
model layer currently prevents a user from typing a password into their free-text
description and having it persisted verbatim in `initial_message`, or the AI
parser from copying a sensitive substring into `facts`. This is a real risk, not
a hypothetical one - see the Threat Model document for the corresponding test
cases, and `evaluations/adversarial_cases.json` for concrete examples the AI parser
must handle correctly (i.e., not persist as a normal field, and ideally not
echo back).

## 3. Data minimization and retention

Following GDPR Article 5(1)(c) (data minimisation) and Article 5(1)(e) (storage
limitation): the system should collect only the fields needed to route a case
through the workflow, and should not retain cases indefinitely by default in a
production version. For this academic MVP:

- No expiry/deletion mechanism currently exists in `Case` (no TTL, no delete
  endpoint). This is acceptable for a prototype but should be listed as a known
  limitation in release documentation - not silently omitted.
- If the project is ever extended past the course MVP, a deletion or expiry
  mechanism should be added before handling real user data.

## 4. Transparency

Users should be told, in plain language, that:
- Their description is processed by an AI model to extract structured facts.
- Recovery *procedures* shown to them come from verified, pre-researched sources -
  not generated or invented by the AI.
- They should not enter passwords, PINs, codes, or financial credentials into the
  description field.

This aligns with the EU AI Act's transparency obligation for AI systems that
interact with users in natural language (commonly discussed as the "limited risk"
category for conversational/classification systems, as opposed to the stricter
"high-risk" category reserved for things like medical diagnosis or law-enforcement
systems). WhatNow does not generate authoritative legal or medical decisions, which
supports treating it as limited-risk rather than high-risk - but this is the
team's own reasoned position for the course project, not a formal legal
determination.

## 5. Ethical risks

- **Hallucination** - AI inventing a procedure, phone number, or source that
  doesn't exist. Mitigated architecturally: procedures must come from Gregorio's
  verified workflow data, never from the LLM directly.
- **Over-reliance / false confidence** - a user may trust an AI-classified case
  summary as complete or official, when fields are still `null`/unknown.
- **Sycophancy** - AI agreeing with an unsafe or incorrect assumption the user
  states confidently (e.g. "I don't need to freeze my bank account, right?").
- **Stale or incomplete sources** - verified workflow data can go out of date;
  someone must own periodic review (Gregorio's audit phase).
- **Accessibility** - the frontend must remain usable under stress (this is a
  crisis-adjacent use case: users are often anxious, possibly in a public place,
  possibly on a damaged/borrowed device).
- **Unequal source quality** - not all regions/situations may have equally
  strong verified sources; unresolved ambiguity should surface as `null`, not be
  papered over.
- **User anxiety** - tone and framing of the UI should be calm and procedural,
  not alarming, since users are already in a stressful situation.

## 6. Summary of legal grounding used

- GDPR Regulation (EU) 2016/679, Article 5 - principles of purpose limitation,
  data minimisation, and storage limitation.
- GDPR Article 25 - data protection by design and by default.
- EU AI Act - four-tier risk classification (unacceptable / high / limited /
  minimal risk); conversational/classification AI systems that do not make
  high-stakes automated decisions typically fall under "limited risk," carrying
  transparency obligations rather than the stricter high-risk regime.

This section reflects the team's understanding of current, publicly available
regulatory guidance for course purposes. It is not legal advice, and no formal
compliance determination is claimed.

## 7. Official sources and verification status

Official sources (found via web search on 2026-09-28):
- GDPR, Regulation (EU) 2016/679, official text on EUR-Lex:
  https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng
  Relevant to this document: Article 5 (principles: purpose limitation, data
  minimisation, storage limitation) and Article 25 (data protection by design
  and by default).
- AI Act, Regulation (EU) 2024/1689, European Commission overview page:
  https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
  Relevant to this document: the risk-based structure and the transparency
  obligations (Article 50).

Verification status and limits:
- The statements in Sections 3 and 4 about GDPR Article 5 and the AI Act are the
  team's summary of these sources. A team member must still open the links above
  and confirm the summary matches the official text. See `ai_logs/marta.md`.
- Whether the AI Act transparency obligations apply to WhatNow depends on the final
  design (for example, whether users interact directly with an AI system). The
  "limited risk" position in Section 4 is the team's own reasoning, not a legal
  determination.
- Application dates and amendments to the AI Act should be checked on the
  Commission page above before any claim about what currently applies is repeated
  in the final report or demo.
