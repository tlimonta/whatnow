# AI Usage Log - Marta Prandin

## Date
2026-09-28

## Tool / model / mode
Claude (Anthropic), Sonnet 5, chat interface, with web search enabled for the
GDPR / EU AI Act part. Used as a planner/tutor and as the drafter of the documents.
No Codex / Claude Code was used for this phase.

## Task
Phase 1 (M1, branch docs/qa-privacy-foundation, issue QA-01): privacy and ethics
analysis, threat model, evaluation plan, acceptance criteria and adversarial test
cases for WhatNow.

## Prompt/context supplied
- The three project guides (Master Project Guide, Phase Gates guide, my Execution Guide).
- Real repository state pasted from my terminal: file tree, `src/models/case.py`,
  `src/backend/schemas.py`, and the existing stub files in `documentation/`.
- I asked the AI to build the documents step by step in the chat.

## Output used
- `documentation/privacy_ethics.md`
- `documentation/threat_model.md`
- `documentation/evaluation_plan.md`
- `documentation/acceptance_criteria.md`
- `evaluations/adversarial_cases.json`
All were drafted by the AI, shown to me in the chat, and saved by me with terminal commands.

## Human verification
- Checked the phase gate: setup PR #1 (chore/project-setup) is merged into main.
- Branched from an up-to-date main; confirmed a clean working tree first.
- Compared the drafts with the real code (`Case` model): the AI found that `facts`
  is an open dictionary and that `initial_message` is stored verbatim with no
  deletion, and these became documented known gaps instead of being hidden.
- Reviewed the file diffs and `git status` after each save.
- Validated the dataset with `python -m json.tool` (valid JSON, 22 cases).
- Checked that all sensitive-looking values in the dataset are fake placeholders.
- Legal / regulatory claims (GDPR Article 5 and 25, EU AI Act): the AI found the
  sources by web search. I then opened the official GDPR text on EUR-Lex and the
  European Commission's AI Act page and checked them against Sections 3 and 4 of
  `privacy_ethics.md` on 2026-09-28. [x] DONE.
  Limit: the "limited risk" position for WhatNow is the team's own reasoning, not a
  legal determination (stated in the document).

## Changes made by human
None. I did not edit the documents by hand; all changes went through the AI chat.

## Problems encountered
- Some multi-line terminal commands did not run the first time (the paste was
  incomplete), so files were not created. `git status` showed this and the commands
  were rerun.
- When staging files for commit, long `git add` lines were split by the paste, so
  the JSON dataset and this log were left out of the first two commits. The JSON
  was committed separately afterwards.
- This log file disappeared from the working folder after I opened it in TextEdit
  (cause not identified) and had to be recreated. Lesson: commit files as soon as
  they are saved, and check `git status` after every step.
- The acceptance criteria thresholds for accuracy metrics are marked PROPOSED,
  because the team has not agreed on them yet and I did not want to invent targets.

## Lesson learned
- Documents written before the system exists can only define what should be tested,
  not report results. Nothing here claims a measured result.
- The biggest unresolved risk is that sensitive text typed into the message field
  is stored as-is (AC-40). It needs a team decision.
