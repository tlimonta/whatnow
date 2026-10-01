# WhatNow source-quality audit

## Scope and method

Audit date: 2026-10-01. Branch: `docs/source-audit`. The audit inspected `data/workflows/stolen_phone_es.json` and `data/sources/stolen_phone_es.json`; the Yoigo source URL was corrected to its canonical form as part of this audit, and no files under `src/` or `tests/` were modified.

The workflow contains nine user-visible actions. Each action was checked against its `source_id`, the corresponding source record, the source authority and domain, the wording of the action, the device/carrier condition, and the `last_verified` date. The linked pages were checked on 2026-10-01 where possible.

## Action-by-action audit

| Action code | Source ID | Authority | Verification date | Status | Notes |
|---|---|---|---|---|---|
| `stolen_phone_es_01` | `policia_nacional_denuncia` | Policía Nacional, Spain | 2026-09-27 | REVIEW | The source supports reporting, identification, the stolen-item list, and IMEI details. The action also mentions an online route for eligible cases, but the separate `policia_nacional_ovd` record is unused by any action. The online eligibility support should be linked explicitly or the wording should remain limited to what the primary source record covers. |
| `stolen_phone_es_02_movistar` | `movistar_bloqueo_linea_robo` | Movistar Spain | 2026-09-27 | PASS | The official page supports suspending the line from the Mi Movistar customer area after theft or loss. The condition correctly limits it to Movistar lines. |
| `stolen_phone_es_03_vodafone` | `vodafone_robo_perdida_dispositivo` | Vodafone España | 2026-09-27 | PASS | The current particulares page supports blocking the SIM and suspending the line through a Vodafone shop, plus requesting a replacement SIM. The action does not incorrectly claim a universal IMEI block. |
| `stolen_phone_es_04_orange` | `orange_robo_perdida_movil` | Orange España | 2026-09-27 | PASS | The official Orange page supports blocking the SIM through Mi Orange, customer support, or a shop. The carrier condition is explicit. |
| `stolen_phone_es_05_yoigo` | `yoigo_robo_perdida_movil` | Yoigo Spain | 2026-09-27 | PASS | Yoigo's official help result supports temporary SIM blocking through Mi Yoigo and replacement-SIM handling. The canonical URL has already been applied in this PR. |
| `stolen_phone_es_06_apple` | `apple_robo_iphone_ipad` | Apple Support España | 2026-09-27 | PASS | The action is correctly conditional on iPhone/iPad and Buscar being enabled. Apple supports marking the device lost, remote erase, the irreversible-erase warning, and retaining Activation Lock. |
| `stolen_phone_es_07_android` | `google_android_perdido` | Google/Android official support | 2026-09-27 | PASS | The action is correctly Android-specific. Google supports Localizador, the listed battery/connectivity/account/visibility prerequisites, remote lost mode, erase, and the loss of location availability after erasure. |
| `stolen_phone_es_08_bank` | `bde_uso_fraudulento_tarjeta` | Banco de España | 2026-09-27 | REVIEW | Banco de España supports physical payment-card fraud: prompt notification, card blocking, police report, and transaction review. It does not establish a universal procedure for banking apps or providers such as Revolut. The workflow wording should be narrowed or supplemented with provider-specific official sources. |
| `stolen_phone_es_09_manufacturer` | `apple_robo_iphone_ipad` | Apple Support España | 2026-09-27 | PASS | AppleCare+ with Theft and Loss confirmed available in Spain, handled by AIG. Optional paid plan, not universal — documented correctly as conditional. |

## Structural and source-registry checks

| Check | Result | Finding |
|---|---|---|
| Every workflow action has a `source_id` | PASS | All 9 of 9 actions contain a non-empty source ID. |
| Every referenced source ID exists | PASS | No orphan source IDs were found. Eight distinct source records are referenced by the nine actions. |
| Unused source records | REVIEW | `policia_nacional_ovd` exists in the registry but is not referenced by any workflow action. It appears relevant to the online-denuncia wording in action `stolen_phone_es_01`. |
| Duplicate source records | PASS | No duplicate source IDs, URLs, or records were found. |
| Verification dates | PASS | All 9 source records have `last_verified: 2026-09-27`; at the audit date they are four days old and recent. |
| Official domains | PASS | URLs use `policia.es`, `denuncias.policia.es`, carrier-owned domains, `support.apple.com`, `support.google.com`, or the Banco de España domain. No blog, Reddit, SEO, or third-party procedure site was found. |
| Spain applicability | PASS with review note | Policía Nacional, the OVD, all four carriers, and Banco de España are Spain-specific. Apple and Google provide official platform guidance in Spanish and are applicable to Spain, but their product availability and terms can vary by country. |
| Device-specific guidance | PASS | Apple and Android actions are separated and conditionally presented. The manufacturer follow-up is explicitly conditional and does not claim universal coverage. |
| Unsupported or overstated action text | REVIEW | Most wording is traceable. The banking action extends beyond the Banco de España source. |

## Summary of issues found

1. **Unused source record:** `policia_nacional_ovd` is not referenced even though action `stolen_phone_es_01` mentions online-report eligibility. This is a traceability gap, not an orphan workflow ID.
2. **Banking scope mismatch:** The Banco de España source is about physical payment-card fraud and card blocking. It does not provide a general banking-app procedure. Provider-specific apps, including Revolut, require direct contact with the provider.
3. **Canonical URL follow-up:** The Yoigo source is on the official Yoigo domain and was found as the official help page. The source registry now uses the canonical URL without the `helpSearch` query parameter.
4. **Documentation consistency:** `documentation/data_sources.md` was updated during this audit so the Vodafone URL and Banco de España description match the current source-quality findings.

## What Gregorio must manually verify

- Decide whether to reference `policia_nacional_ovd` from the workflow action or remove it from the source registry. This audit modified the source JSON only to correct the Yoigo URL to its canonical form; workflow JSON was not modified.
- Narrow the banking action to payment-card exposure or add official sources for each supported banking/payment provider. Do not present Banco de España as a universal banking-app procedure.
- If the workflow is later extended beyond AppleCare+, add official Spain-applicable sources for additional manufacturers or insurers.
- Recheck the canonical Yoigo page remains current before a future data update.
- Recheck carrier menus, identity checks, replacement-SIM rules, and source pages immediately before committing or releasing the workflow.

## Audit conclusion

The workflow has a solid source-linked structure and no missing referenced source IDs or duplicate source records. Seven actions pass as currently worded. Two actions require source-scope review before the workflow should be treated as fully audited: the online-denuncia traceability and the generic banking-app wording.
