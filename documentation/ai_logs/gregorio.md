# Gregorio Cerini: AI usage log

## Date

2026-09-27

## Tool/model/mode

OpenAI Codex, default collaboration mode, with web research and local repository file editing.

## Task

Create a verified Spain stolen-phone workflow, its authoritative source registry, research documentation, data-source documentation, and this AI usage log. Do not commit, push, create or switch branches, add secrets, or edit files outside the five requested paths.

## Prompt/context supplied

Project: WhatNow (DAT32-91 Prompt Engineering and Git). The MVP helps users navigate stressful administrative situations. Structured verified workflow data determines applicable actions; AI must not generate authoritative recovery procedures. Gregorio Cerini's role is verified sources, workflow data, and source-quality audit. The requested workflow had to cover a police report, SIM blocking for Movistar/Vodafone/Orange/Yoigo, Apple/Google remote controls, bank contact when banking apps are installed, and manufacturer contact when needed. Every workflow step needed a source reference, and every referenced source needed a URL and `last_verified` date of 2026-09-27.

## Output used

- Created `data/workflows/stolen_phone_es.json` with nine source-linked, conditional or general workflow steps.
- Created `data/sources/stolen_phone_es.json` with nine official or authoritative source records.
- Created `documentation/research/stolen_phone_spain.md` with the research method, source-selection rationale, decisions, limitations, and manual review checklist.
- Replaced the placeholder content in `documentation/data_sources.md` with the source URLs and one-line descriptions.
- Created this log at `documentation/ai_logs/gregorio.md`.

## Human verification needed

Gregorio must open the linked pages and confirm current procedures, especially Vodafone's customer-segment page, carrier menus and identity requirements, the eligibility and ratification rules for online police reports, and the Apple/Google remote-control prerequisites. He must also confirm whether the product should add manufacturer- or insurer-specific sources beyond the AppleCare+ example. The bank step needs product-owner review because the authoritative source directly covers payment cards and unauthorized transactions, not one universal banking-app deactivation procedure.

## Problems encountered

- No single official source provides one universal Spanish procedure for all carriers, so SIM suspension was split into four carrier-specific steps.
- SIM suspension and IMEI handset blocking are different actions; carrier guidance varies, so a universal IMEI-block step was not added.
- The Banco de España guidance is strongest for lost or stolen payment cards. It supports prompt bank contact, blocking, reporting, and checking movements, but not a universal action for every banking app.
- Apple documents a specific AppleCare+ theft-and-loss claim, while manufacturer support and coverage are not standardized across brands.

## Lesson learned

Keep authoritative actions narrow and source-linked. When a source supports only a related security action, encode the step as conditional and document the boundary instead of filling the gap with plausible but unverified instructions.
