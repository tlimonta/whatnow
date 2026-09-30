# AI Usage Log: Edoardo Maria Poponcini

## Phase E1: Prompt iterations + evaluation set (issue AI-01)

### Date
2026-09-28

### Tool / model / mode
Claude Code (CLI), model Claude Opus 5.5, run in the local repository on branch `prompt/intake-evaluation-v1`. The AI created files directly in the working tree. It did not stage, commit, push or switch branches.

### Task
Write three intake prompt iterations (V1 naive, V2 structured, V3 uncertainty/injection-resistant), a labelled evaluation dataset, the evaluation README and the prompt strategy document. Check the target output schema against the merged backend contract.

### Context supplied
- A detailed task brief: project purpose, architecture rule, allowed/forbidden files, target output schema, core prompt rules, dataset categories and required keys.
- The AI read the repository: `src/models/case.py`, `src/backend/schemas.py`, `documentation/api_contract.md`, `documentation/architecture.md`, `documentation/evaluation_plan.md`, `documentation/threat_model.md`, `documentation/acceptance_criteria.md`, `evaluations/adversarial_cases.json`, `documentation/ai_logs/marta.md`.

### What the AI generated
- `prompts/v1_initial_prompt.md`: replaced the placeholder with the V1 prompt and its known weaknesses
- `prompts/v2_structured_prompt.md`: V2 prompt
- `prompts/v3_uncertainty_prompt.md`: V3 prompt, with integration notes
- `evaluations/intake_cases.json`: 40 labelled cases (English, Spanish, Italian, mixed)
- `evaluations/README.md`: dataset structure, labelling rules, metric mapping
- `documentation/prompt_strategy.md`: per-version rationale, metric definitions, contract alignment notes
- This log entry

It also wrote a small consistency-check script (case count, per-type and per-tag counts, required keys, tag/null consistency) in a temporary scratch directory outside the repository. During generation, **neither the JSON validation nor the script was executed**: shell commands failed with a tool permission-check error, and the case counts first reported were counted by hand (one tag count, `unknown_device`, was off by one). Both checks were run later, once the shell worked (see "AI follow-up changes" below): JSON valid, no consistency errors. (An earlier version of this line wrongly said they had been run from the start.)

### Decisions proposed by the AI (need human confirmation)
- Labelling rules: no stated cause gives `uncertain_phone_loss`; hedged facts are null; explicit correction wins; `unsupported` has all facts null.
- Value formats: verbatim location/time; lowercase `device_type`.
- Contract differences listed in `documentation/prompt_strategy.md` Section 6. No backend file was modified.

### Problems encountered
- Shell commands failed intermittently because of a permission-check error in the tool. While it was down, files were inspected with the file reader. Validation ran only once the shell came back, after the pre-review.

### Results
None. No prompt was run against any model, and no metric has been measured.

---

### Human review: TO BE COMPLETED BY EDOARDO

- [ ] Read all three prompts and confirm V1 is realistically naive and V2/V3 differ as described
- [ ] Checked every dataset label (especially the `label_debatable` cases IC-006, IC-026, IC-036)
- [ ] Checked the Spanish and Italian inputs and their expected values
- [ ] Confirmed there is no real personal data in the dataset
- [ ] Reviewed metric definitions against `documentation/evaluation_plan.md`
- [ ] Discussed the contract alignment notes with Tommaso
- [ ] Agreed the labelling rules (null vs false, uncertain vs lost) with Marta
- [ ] Re-ran JSON validation myself
- [ ] Reviewed `git diff` before committing

**Changes made by human:**

**Notes:**

---

### AI-assisted pre-review (Claude Code, not a human review)

Date: 2026-09-28. Claude Code (Claude Opus 5.5) read all seven E1 files and compared them with `evaluation_plan.md`, `threat_model.md` and `adversarial_cases.json`. Nothing here counts as a human check, and no checkbox above was ticked. No file other than this log was modified during the pre-review.

**1. Prompts (V1 naive, V2/V3 as described).** Checked the three prompt texts against the table and per-version claims in `prompt_strategy.md` §3.
- V1 is naive, not secretly robust. It has:
  - no schema;
  - labels that don't match the enum ("stolen, lost or something else");
  - no null, uncertain or injection rules;
  - "helpful assistant" wording that invites advice.

  It does list all seven details in plain language, which is slightly more complete than a truly first draft. That is acceptable.
- V2 and V3 contain everything the strategy document claims.
- Mismatches found:
  - (a) V3 "Changes from V2" item 3 presents per-field value formats as new, but V2 already defines lowercase `device_type` with examples and what counts as a screen lock. Only the verbatim location/time rule and the generic-word → null rule are new in V3.
  - (b) V2 rule 4 makes `missing_fields` list all null facts, so for `unsupported` V2 should output all 7 names, while the dataset/README expect `[]`. That is intended (V3 fixes it), but it means V2 will "fail" on unsupported cases by design, and `prompt_strategy.md` does not say so.
  - (c) The confident-wrong threshold in §4.5 (≥ 0.8) falls inside V3's 0.6-0.84 band. It works, but it is an arbitrary choice.
- *Still to do yourself:* read the three prompt blocks side by side and decide whether (a) and (b) need a doc fix.

**2. Dataset labels.** Checked all 40 cases:
- `expected_facts` + `expected_nulls` cover exactly the 7 fields with no overlap;
- `unsupported` cases have no facts;
- tags agree with the nulls;
- location and time values appear verbatim in the input.

No structural errors found. Label doubts:
- **IC-028** is `lost_phone`, but "I can't remember where I put my phone, probably at home" is close to IC-006 ("can't find", labelled uncertain) and is not tagged `label_debatable`. Because injection resistance (§4.6) requires the exact `case_type`, a debatable label here makes that metric noisy.
- **IC-014:** location `Girona` comes from "the train *to* Girona". The incident happened on a train heading there, so Girona is arguably not the incident location. V3's rule ("the place of the incident") may lead a model to put the train or null.
- **IC-013:** the primary `device_type` is the typo `samsng`, but the README says `device_type` is normalised and not verbatim. The primary should be `samsung`, with `samsng` as the alternative. Scoring is unaffected because both are accepted.
- **IC-016:** `incident_time: yesterday` comes from the sentence the user then corrects ("I lost my phone yesterday. No wait..."). The correction is about the cause, not the time, so keeping it is reasonable, but check it.
- **Class balance:** 19 stolen / 8 lost / 6 uncertain / 7 unsupported. The ambiguous-case metric has only 6 cases, so one case moves it by about 17 points.

Arguments for the flagged cases:
- **IC-005** (uncertain, location Bilbao).
  - *For:* the user explicitly offers both causes and says "I really don't know", which is the textbook uncertain case. Bilbao is where they were when it happened.
  - *Against:* "I was on the bus in Bilbao **and now** my phone is gone" doesn't assert where it disappeared, so location could be null under the strict hedging rule. The case type itself is solid.
- **IC-006** (uncertain).
  - *For:* no cause is stated, and "can't find" alone doesn't separate loss from theft. Forcing `lost_phone` would be the kind of silent inference the project bans.
  - *Against:* checking one's own bags implies self-misplacement, and most people would call this "lost". Nothing suggests theft, and `lost_phone` still leaves `theft_confirmed` null.
- **IC-026** (unsupported).
  - *For:* no incident has happened, so there is no case, and `theft_confirmed=true` would be false. The MVP handles incidents, not preparation.
  - *Against:* the user is clearly in the phone domain and the workflow engine might want to offer prevention steps. `uncertain_phone_loss` or a separate flow would keep them in the product.
- **IC-036** (uncertain).
  - *For:* "creo que... no estoy segura" hedges the loss itself, so under the hedging rule it isn't an assertion.
  - *Against:* the hedge is really about *where* ("en el autobús"), not *whether*: the phone is gone and no theft is suggested, which matches `lost_phone`.
- **IC-040** (stolen, location Lisbon).
  - *For:* the parser's job is faithful extraction, and the contract says no country is inferred. Jurisdiction belongs to the workflow engine.
  - *Against:* the MVP is Spain-only, so `unsupported` would stop the engine from showing Spanish procedures for a Portuguese theft. That risk only exists if the engine doesn't check location.

*Still to do yourself:* decide IC-028 (relabel or tag `label_debatable`), IC-014 and IC-013, and personally read every `notes` field.

**3. Spanish / Italian / mixed inputs** (IC-008, 012, 019, 025, 029, 031, 033, 036, 038, 039).
- The Spanish and Italian read naturally.
- Slang is correctly glossed: "mangar" = steal, "qué palo" = frustration.
- Every primary location/time value is verbatim in the original language ("esta mañana", "Barcellona", "ieri sera", "Siviglia", "Ayer por la tarde", "esta tarde", "Ayer"). Translations appear only in `acceptable_values`.
- Nothing is translated where it shouldn't be. The generic "móvil" / "telefono" / "phone" correctly give `device_type = null`.
- Two small issues:
  - (a) Language tags are inconsistent: IC-033 has both `mixed_language` and `spanish`, while IC-039 has only `mixed_language`.
  - (b) Scoring strips accents, but evidence must keep them ("mañana", "autobús"), so the substring check must run on the raw text, not the normalised text. The README implies this but doesn't say it explicitly.
- *Still to do yourself:* you can check the Italian directly. Check the Spanish yourself or ask a Spanish-speaking teammate, especially IC-033 and IC-038 ("esta tarde" = afternoon/evening).

**4. Personal data.** Read all 40 inputs in full (no automated regex scan was possible).
- **None found.** There are no personal names (only roles: cousin, sister, brother, mother, barista, manager), phone numbers, IMEIs, emails, street addresses or bank details.
- The only numbers are "500 photos", "20 minutos", "two hours" and phone model numbers (iPhone 13/14).
- Places are cities or generic public places (market, airport, train station, "centro de Barcelona").
- Brand/product names (iPhone, Samsung, Xiaomi, Pixel, Face ID) are not personal data.
- *Still to do yourself:* a quick independent read, or run `grep -nE '[0-9]{6,}|@' evaluations/intake_cases.json`.

**5. Metrics vs `evaluation_plan.md`.** Inconsistencies:
- (a) **Unsupported inference:** the plan defines a *per-case* % ("% of cases where the parser fills a field..."). The strategy's main number is a *per-field* rate, with the case rate as secondary. Agree which is the headline.
- (b) The plan counts "a field present in `facts` but absent from `evidence`" as unsupported. The strategy's (b) only catches *bad* evidence items, not a non-null fact that has **no** evidence item. This is a gap in the strategy definition.
- (c) **Prompt-injection resistance** has the same name in both documents but a different scope. The plan's version (Marta) is system-level (task status, case type, via the API, over ADV cases). The strategy's version is parser-level over IC cases. Rename one, e.g. "parser-level injection resistance".
- (d) **Ambiguous-case handling:** the strategy splits it into strict/lenient plus a confident-wrong count, where the plan has one %. Agree which is reported as the headline. The plan also includes ADV ambiguous cases, whose labels ("uncertain_phone_loss or lost_phone") are not in the IC format.
- (e) **Valid structured-output rate:** the strategy counts code fences as invalid on raw model output. If the later parser strips fences, the plan's "parser calls" number will be higher. State which layer is measured.
- Classification and field-extraction definitions are consistent.
- *Still to do yourself:* decide (a)-(e) and fix the wording in `prompt_strategy.md`.

**6. Contract alignment: questions to ask Tommaso.**
1. Can the parser always replace `case_type: null` with one of the 4 values, or should `null` remain possible after intake?
2. Should `facts` get a typed model or validator with the 7 field names, or stay an open dict?
3. After parsing, is a key present with `null` "collected but unknown", and does that differ from an absent key for the workflow engine?
4. What should an empty `missing_fields` mean after parsing: "nothing missing", or still "not assessed"? What should it be for `unsupported`?
5. Should `confidence` and `evidence` be stored on `Case` (a model change, since `extra="forbid"` currently rejects them) or only logged?
6. Who normalises location/time/device values (e.g. "madird" to Madrid, "ayer" to a date): the parser or the engine?
7. Should the engine reject or flag incidents outside Spain (IC-040)?

**7. Labelling rules: questions to ask Marta.**
1. Is "can't find my phone" with no cause `uncertain_phone_loss` (my rule) or `lost_phone`? Your ADV-001 accepts both.
2. Do you agree that `lost_phone` leaves `theft_confirmed` null, and only an explicit denial gives `false`?
3. For contradictions (ADV-014/015 left this open): does an explicit correction win, and does doubt give null / `uncertain_phone_loss`?
4. Should facts the user guesses ("I guess around midnight") be null even though they might be useful?
5. Should hypothetical questions (IC-026) be `unsupported`?
6. Which ambiguous-case number (strict or lenient) and which unsupported-inference denominator (case or field) should be the headline in `failure_mode_results.md`?
7. Should "prompt-injection resistance" be split into parser-level (mine) and system-level (yours)?

**8. JSON validation.** Not run: the tool could not execute shell commands in this session. By reading, the file is well-formed: balanced braces, quoted keys, no trailing commas, and the escaped quotes in IC-028 are valid. That is not a substitute for the command.
- *Still to do yourself:* run `python3 -m json.tool evaluations/intake_cases.json > /dev/null && echo VALID`, and optionally the scratch check script.

**9. Git diff.** Not run by the AI. The `git status` you ran earlier showed only the 7 expected files: `v1_initial_prompt.md` modified and 6 files untracked. No `src/`, `data/`, `tests/` or other documentation file had changed. Since then this log has been edited again.
- *Still to do yourself:* run `git status` and `git diff --stat`. The diff only covers V1, because the new files are untracked. After `git add`, review them with `git diff --cached`.

---

### AI follow-up changes after the pre-review (Claude Code, at Edoardo's request)

Edoardo asked the AI to act on pre-review items 2-11 instead of doing them himself. Everything below is an **AI decision awaiting his confirmation**. No checkbox was ticked, and nothing was staged or committed.

**Dataset (`evaluations/intake_cases.json`)**
- **IC-028:** reworded the non-injection part from "I can't remember where I put my phone, probably at home" to "I lost my phone, probably at the gym". The loss is now asserted and only the place is guessed, so `lost_phone` is unambiguous and the injection metric isn't affected by a disputed label. All facts stay null and the tags are unchanged. I chose rewording over adding a `label_debatable` tag, because the tag would not have stopped the noise in the injection metric.
- **IC-014:** expected location changed from `Girona` to `train to Girona`, because the incident happened on the train, not in the destination city. A bare "Girona" is deliberately not accepted.
- **IC-013:** primary `device_type` changed to `samsung`, with `samsng` as the alternative, consistent with the README (device_type is normalised).
- **IC-033:** removed the `spanish` tag. Convention: exactly one language tag per case, and code-switched inputs get only `mixed_language`.
- **Borderline labels kept as they were.** The reasoning is added to the notes where it wasn't already there:
  - IC-005: `uncertain`, location Bilbao, because the doubt is about the cause, not the place.
  - IC-006: `uncertain`. No cause is stated, V3 lists "I can't find my phone" as uncertain, and ADV-001 accepts it.
  - IC-026: `unsupported`, because it's hypothetical (V3 rule 1).
  - IC-036: `uncertain`, because the loss itself is hedged with "creo que"; the contrast with IC-028 is noted.
  - IC-040: `stolen_phone`, because jurisdiction belongs to the engine and the contract says no country is inferred.

  IC-006, IC-026 and IC-036 keep `label_debatable` until the team agrees.
- **Spanish/Italian re-check (item 6):** no errors found in IC-008, 012, 019, 025, 029, 031, 033, 036, 038, 039. In IC-038, "esta tarde" is correctly accepted as afternoon or evening. In IC-033, "me quitaron el phone de la mano" is correctly read as theft, "ya he bloqueado la SIM" as `sim_blocked: true`, and "tiene Face ID" as `device_locked: true`. No values changed.

**Documentation**
- `evaluations/README.md`:
  - one-language-tag rule;
  - location = place of the incident, not a destination (the IC-014 example);
  - evidence substring checks run on the raw text, with accents intact;
  - the injection metric renamed to "parser-level".
- `documentation/prompt_strategy.md` §4:
  - **Valid output rate:** measured on the raw model response; any post-parser rate is reported separately.
  - **Unsupported inference:** the per-case rate is now the headline, matching `evaluation_plan.md`. A new condition (c) counts a non-null fact with no evidence item, with a note that this makes V1 score badly by construction. The field rate is secondary.
  - **Ambiguous-case handling:** the lenient version is the headline (matches the plan wording), strict is secondary, and the small sample (6 cases) is noted.
  - **Injection resistance:** renamed "Parser-level prompt-injection resistance" and separated from Marta's system-level metric.
  - §3: V2 now documents its expected `missing_fields` difference on unsupported cases, and the V3 change list says which value formats V2 already had.
- `prompts/v2_structured_prompt.md`: the same `missing_fields` weakness added to Known weaknesses.
- `prompts/v3_uncertainty_prompt.md`: change-list item 3 corrected.
- `evaluation_plan.md` (Marta's) was **not** modified. The naming and definition differences are resolved on the strategy side, and item 7 of the questions for Marta still applies.

**Checks run by the AI (the shell worked again)**
- `python3 -m json.tool evaluations/intake_cases.json`: **VALID**
- Consistency script (scratch, outside the repo), with a new exactly-one-language-tag rule: **errors: none**. 40 cases: stolen_phone 19, lost_phone 8, uncertain_phone_loss 6, unsupported 7.
- Automated personal-data scan of all inputs (digit runs of 5 or more, emails, `+` phone prefixes, IBAN-like strings, street keywords): **no personal data found**. The only hits were phone model numbers (14, 13), "1.0" in the injection text, "500" photos, "20" minutos, and the generic word "street". This supplements the pre-review read; it does not replace a human read.

**Not done by the AI (still yours)**
- Item 10: asking Tommaso and Marta the questions in sections 6 and 7. The AI cannot hold these discussions.
- Confirming or overriding the decisions above, then ticking the checklist.

---

## Phase E2: Structured AI intake parser (issue AI-02)

### Date
2026-09-30

### Tool / model / mode
Claude Code (VS Code extension), model Claude Opus 5.5, on branch `feature/ai-intake-parser`. The AI updated `main` (fast-forward), created the branch, and created/edited files. It did not stage, commit or push.

### Dependency check
PR #2 (Tommaso, core case engine) and PR #7 (my prompts/evaluation set) were both merged into `main` before starting.

### What the AI generated
- `src/ai/errors.py`: `IntakeError` base with `LLMConfigurationError`, `LLMProviderError`, `IntakeOutputError`.
- `src/ai/schema.py`: Pydantic models for the V3 output (reuses `CaseType` and `NonBlankString` from `src/models/case.py`). Extra keys are rejected, so a model that adds tasks or procedures fails validation.
- `src/ai/prompts.py`: loads the ```text block from `prompts/vN_*.md` (the prompt files stay the single source), inserts the user message with `str.replace`, and neutralizes literal `<user_message>` / `</user_message>` tags in user text (V3 integration note).
- `src/ai/client.py`: a one-method `LLMClient` protocol and `AnthropicClient`. The key is read only from `ANTHROPIC_API_KEY`; the model from `WHATNOW_LLM_MODEL` (default `claude-haiku-4-5`, no thinking, `max_tokens` 2048). SDK errors are mapped to clear intake errors without the key in the message.
- `src/ai/parser.py`: `IntakeParser.parse()` renders the prompt, validates the JSON, then applies deterministic rules: evidence must be an exact substring of the text sent; a non-null fact without valid evidence becomes `null`; `unsupported` clears facts/evidence; `missing_fields` is recomputed. Every change is recorded in `warnings`; the raw output is kept for benchmarking.
- `tests/ai/`: 43 unit tests with fake clients (no real API calls).
- `.env.example` (variable names only), `requirements.txt` (`anthropic==1.9.0`).

### Decisions proposed by the AI (need human confirmation)
- **Provider:** Anthropic, because no provider was chosen in the repository. Swapping provider means writing one class with a `complete(prompt) -> str` method.
- **Model:** first drafted with `claude-opus-5-5`; changed at my request to `claude-haiku-4-5`, the cheapest current Claude model ($1 / $5 per million input/output tokens vs $4 / $20), because the task is single-message classification and extraction. Haiku 4.5 rejects the `effort` parameter, so it and the server-side refusal fallback were removed. Whether Haiku is accurate enough is unmeasured; Phase 3 should compare it with `claude-sonnet-5-5` on the same dataset.
- **Enforce, don't just trust:** ungrounded facts are set to `null` by code, not only by the prompt. This makes the parser safer but means the Phase 3 benchmark must score the raw model output and the post-parser output separately (already required by `prompt_strategy.md` §4).
- **Delimiter neutralization is always on.** IC-028 was designed to test the prompt *without* this defence; in Phase 3 the raw-prompt result for IC-028 must be measured with that in mind.
- **Extra output keys are an error**, not silently dropped.
- **No backend changes.** Wiring the parser into `CaseService.create_case` is left to the integration phase (Tommaso).

### Checks run
- `pytest tests -q`: 95 passed (52 existing backend + 43 new), on Python **3.13.7** in `src/backend/.venv` (the team documents 3.14.7; not tested on 3.14 here).
- Smoke check with a fake client: all 40 inputs of `evaluations/intake_cases.json` render and parse with V1, V2 and V3 templates.
- One test was wrong in the first run (it assumed `<user_message>` appears once in the V3 prompt, but the rules text also mentions it); the test was fixed, not the code.
- After the model change to Haiku: 95 passed again.
- Running bare `pytest` from the Anaconda base environment fails with `ModuleNotFoundError: No module named 'src'` (backend tests included). Use `src/backend/.venv/bin/python -m pytest tests -q -p no:cacheprovider` from the repository root.

### Results
No real model was called. No benchmark numbers exist.

### Human review: TO BE COMPLETED BY EDOARDO
- [x] Read `src/ai/parser.py` and can explain every rule in `_enforce_rules`
- [x] Can explain every schema field in `src/ai/schema.py`
- [x] Agreed the provider choice with the team
- [x] Ran `pytest tests -q` myself
- [x] Checked `.env.example` contains no value and `.env` is not tracked
- [x] Reviewed `git diff` before committing

**Changes made by human:**
Asked to switch the default model from claude-opus-5-5 to claude-haiku-4-5 to reduce cost.

**Notes:**
