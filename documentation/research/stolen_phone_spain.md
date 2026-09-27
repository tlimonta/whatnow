# Research: stolen phone workflow in Spain

## Scope and method

Research was completed on 2026-09-27 for the WhatNow MVP. The workflow is deliberately limited to actions supported by official or authoritative sources. I searched for primary guidance from Spanish law-enforcement bodies, the four named Spanish carriers, the device-platform manufacturers, and the Banco de España. Search-result summaries were used to locate pages; the linked pages were then checked for the actual procedure and its conditions.

The workflow does not ask the language model to invent a recovery procedure. It uses `source_id` values to connect every action to a record in [`data/sources/stolen_phone_es.json`](../../data/sources/stolen_phone_es.json).

## Sources chosen

| Source ID | Why it was chosen | Workflow use |
|---|---|---|
| `policia_nacional_denuncia` | Policía Nacional is an official Spanish law-enforcement source. Its denunciation guidance says a person can attend a police station and should bring identification and a list of stolen items, including make, model, serial number, and IMEI when available. | Filing the denuncia and preserving the IMEI as identifying information. |
| `policia_nacional_ovd` | The Policía Nacional Oficina Virtual de Denuncias is the official online service and states the categories and exclusions for complaints that can be started online. | Limiting the online-denuncia wording to eligible cases. |
| `movistar_bloqueo_linea_robo` | Movistar's own customer guidance explicitly describes suspending a mobile line after theft or loss and separately recommends reporting the theft. | Conditional Movistar SIM/line suspension. |
| `vodafone_robo_perdida_dispositivo` | Vodafone's official help page describes blocking the SIM and suspending the line after loss or theft, including the route through a Vodafone shop and a replacement SIM. | Conditional Vodafone SIM/line suspension. |
| `orange_robo_perdida_movil` | Orange's official help page gives an explicit Mi Orange path to “Bloquear SIM” and lists official support/shop routes. | Conditional Orange SIM blocking. |
| `yoigo_robo_perdida_movil` | Yoigo's official help page gives an explicit Mi Yoigo path to temporary SIM blocking and a replacement-SIM route. | Conditional Yoigo SIM blocking. |
| `apple_robo_iphone_ipad` | Apple is the device manufacturer and documents Lost Mode, remote erase, keeping the device in Buscar, operator/authority contact, and AppleCare+ with Theft and Loss claims. | Conditional Apple remote protection/erase and manufacturer coverage follow-up. |
| `google_android_perdido` | Google/Android is the platform authority for Localizador. The page documents remote location, marking as lost, erasure, prerequisites, and the post-erasure location limitation. | Conditional Android remote protection/erase. |
| `bde_uso_fraudulento_tarjeta` | Banco de España is Spain's central bank and its consumer guidance says to notify the entity immediately, request a block, report the theft, and check account movements for a lost or stolen payment card. | Conditional bank contact when payment or banking access may be exposed. |

## Resulting workflow decisions

1. The denuncia is the first general step because the Policía Nacional source supports reporting the theft and supplying the IMEI where available.
2. SIM suspension is represented as four carrier-specific conditional steps. A user should see only the carrier matching the affected line.
3. Apple and Android are separate conditional steps because their remote-control tools and prerequisites differ.
4. The bank step tells the user to contact the bank immediately but does not claim that every bank has the same app-disabling process. The source directly supports blocking payment cards and checking transactions; it does not provide one universal rule for all banking apps.
5. Manufacturer support is a conditional follow-up. Apple documents an AppleCare+ theft-and-loss claim, but no universal manufacturer-reporting process applies to every phone brand or insurance plan.

## Ambiguities and limitations

- **Online denuncia eligibility:** Policía Nacional's online service excludes some situations, including violence or intimidation, known perpetrators, witnesses, and crimes in progress. A person in an excluded situation should use the appropriate in-person or emergency route. The workflow therefore says “eligible cases” rather than presenting online reporting as universal.
- **Police service differences:** The sources reviewed include Policía Nacional guidance; the exact route may also depend on the local competent authority and facts of the incident. No claim is made that one online form covers every Spanish jurisdiction.
- **SIM versus IMEI:** SIM suspension stops use of the affected line; it is not the same as blocking the handset by IMEI. The carrier pages describe different IMEI requirements and timing, so an IMEI block was not added as a universal workflow step. The police step still asks users to provide the IMEI when available.
- **Carrier account variation:** Menus, identity checks, replacement-SIM fees, and customer channels can vary by contract type and may change. The workflow links to the carrier's current page instead of hard-coding phone numbers.
- **Remote controls are conditional:** Apple requires Buscar to have been enabled before the theft. Google lists battery, connectivity, Google Account, Localizador, and Google Play visibility prerequisites. Remote erase is consequential: Apple describes it as irreversible, and Google says location is unavailable after erasure.
- **Banking apps:** The Banco de España source is strongest for payment cards and unauthorized transactions. It does not prescribe one cross-bank action for an installed banking app. The workflow therefore requires contact with the bank and leaves the bank to determine the security action.
- **Banking-app provider limitation:** Banco de España source covers physical payment card fraud only; does not cover general banking app procedures. For apps like Revolut, users must contact their specific provider directly.
- **Manufacturer reporting:** AppleCare+ with Theft and Loss is an example of a manufacturer-specific coverage route, not a universal obligation. Android-device manufacturer support and insurer terms require separate verification before adding a more specific step.
- **Freshness:** Carrier help pages and platform interfaces can change. The `last_verified` date records this research pass, not a guarantee that the URLs or menus remain unchanged.

## Manual verification before release

Gregorio should open each linked source, confirm that the wording and eligibility conditions still match the workflow, verify Vodafone coverage for the intended customer segment, and decide whether the product should add a separate insurer or manufacturer-specific data source. The bank step should be reviewed with the product owner so it remains a prompt to contact the bank rather than an invented banking-app procedure.
