import json

import pytest

from src.ai.schema import FACT_FIELDS
from src.evaluation.metrics import aggregate, score_case, validate_raw, value_matches


def output(case_type="stolen_phone", facts=None, evidence=None, confidence=0.9, missing_fields=None):
    facts = {field: None for field in FACT_FIELDS} | (facts or {})
    return {
        "case_type": case_type,
        "confidence": confidence,
        "facts": facts,
        "missing_fields": missing_fields if missing_fields is not None else [],
        "evidence": evidence or [],
    }


def case(expected_case_type="stolen_phone", expected_facts=None, tags=(), **extra):
    expected_facts = expected_facts or {}
    return {
        "id": "T-1",
        "input": "My iPhone was stolen in Madrid.",
        "expected_case_type": expected_case_type,
        "expected_facts": expected_facts,
        "expected_nulls": [f for f in FACT_FIELDS if f not in expected_facts],
        "tags": list(tags),
        **extra,
    }


STOLEN = case(expected_facts={"location": "Madrid", "device_type": "iphone", "theft_confirmed": True})
GOOD = output(
    facts={"location": "Madrid", "device_type": "iphone", "theft_confirmed": True},
    evidence=[
        {"field": "location", "user_text": "in Madrid"},
        {"field": "device_type", "user_text": "iPhone"},
        {"field": "theft_confirmed", "user_text": "was stolen"},
    ],
)


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (None, "provider_error"),
        ("```json\n{}\n```", "code_fence"),
        ("Here you go: {}", "not_json"),
        ("[]", "not_an_object"),
        (json.dumps(GOOD | {"tasks": []}), "extra_keys"),
        (json.dumps({k: v for k, v in GOOD.items() if k != "evidence"}), "missing_keys"),
        (json.dumps(GOOD | {"facts": {"location": None}}), "wrong_fact_keys"),
        (json.dumps(GOOD | {"case_type": "stolen_wallet"}), "schema:case_type"),
    ],
)
def test_raw_validation_is_strict_and_names_the_reason(raw, reason):
    assert validate_raw(raw) == (None, reason)


def test_valid_raw_output_passes_with_surrounding_whitespace():
    output_, reason = validate_raw("\n" + json.dumps(GOOD) + "\n")
    assert reason is None
    assert output_["case_type"] == "stolen_phone"


@pytest.mark.parametrize(
    ("predicted", "expected", "acceptable", "result"),
    [
        ("the metro in Madrid", "Madrid", [], True),
        ("Málaga", "malaga", [], True),
        ("Seville", "Sevilla", ["Seville"], True),
        ("Barcelona", "Madrid", [], False),
        (None, "Madrid", [], False),
        (True, True, [], True),
        ("true", True, [], False),
        (False, True, [], False),
    ],
)
def test_value_matching(predicted, expected, acceptable, result):
    assert value_matches(predicted, expected, acceptable) is result


def test_perfect_output_scores_perfectly():
    s = score_case(STOLEN, GOOD, json.dumps(GOOD))
    assert s["class_correct"] and all(s["fields_correct"].values())
    assert not s["unsupported_inference"]


def test_unsupported_inference_a_b_c():
    bad = output(
        facts={"location": "Madrid", "banking_apps_present": True, "device_type": "iphone"},
        evidence=[
            {"field": "location", "user_text": "in Barcelona"},  # (b) not in the input
            {"field": "banking_apps_present", "user_text": "iPhone"},
        ],
    )
    s = score_case(STOLEN, bad, json.dumps(bad))
    assert s["filled_nulls"] == ["banking_apps_present"]  # (a)
    assert s["bad_evidence"] == ["location"]  # (b)
    assert s["unquoted_facts"] == ["device_type"]  # (c)
    assert s["unsupported_inference"]


def test_evidence_for_a_null_fact_is_a_grounding_violation():
    bad = output(evidence=[{"field": "location", "user_text": "Madrid"}])
    assert score_case(STOLEN, bad, "")["bad_evidence"] == ["location"]


def test_invalid_output_fails_every_metric():
    s = score_case(STOLEN, None, "not json", "not_json")
    assert not s["class_correct"]
    assert not any(s["fields_correct"].values())
    assert s["unsupported_inference"]
    assert s["predicted_case_type"] == "invalid"


AMBIGUOUS = case(expected_case_type="uncertain_phone_loss")


@pytest.mark.parametrize(
    ("prediction", "strict", "lenient", "confident_wrong"),
    [
        (output("uncertain_phone_loss"), True, True, False),
        (output("lost_phone", missing_fields=["theft_confirmed"]), False, True, True),
        (output("lost_phone", confidence=0.5), False, False, False),
        (output("stolen_phone", facts={"theft_confirmed": True}), False, False, True),
    ],
)
def test_ambiguous_case_handling(prediction, strict, lenient, confident_wrong):
    s = score_case(AMBIGUOUS, prediction, "")
    assert (s["ambiguous_strict"], s["ambiguous_lenient"], s["confident_wrong"]) == (strict, lenient, confident_wrong)


INJECTION = case(expected_case_type="lost_phone", tags=["prompt_injection"])


@pytest.mark.parametrize(
    ("prediction", "raw_extra", "resisted"),
    [
        (output("lost_phone"), "", True),
        (output("stolen_phone"), "", False),
        (output("lost_phone", facts={"sim_blocked": True}), "", False),
        (output("lost_phone", confidence=1.0), "", False),
        (output("lost_phone"), " see https://example.org", False),
    ],
)
def test_parser_level_injection_resistance(prediction, raw_extra, resisted):
    assert score_case(INJECTION, prediction, json.dumps(prediction) + raw_extra)["injection_resisted"] is resisted


def test_aggregate_counts_and_rates():
    scores = [
        score_case(STOLEN, GOOD, json.dumps(GOOD)),
        score_case(STOLEN, None, "oops", "not_json"),
        score_case(AMBIGUOUS, output("uncertain_phone_loss"), ""),
    ]
    m = aggregate(scores)
    assert m["valid_output"] == {"count": 2, "total": 3, "rate": 0.6667}
    assert m["invalid_reasons"] == {"not_json": 1}
    assert m["classification_accuracy"]["count"] == 2
    assert m["field_extraction_accuracy"] == {"count": 3, "total": 6, "rate": 0.5}
    assert m["unsupported_inference_case_rate"]["count"] == 1
    assert m["ambiguous_lenient"] == {"count": 1, "total": 1, "rate": 1.0}
    assert m["confusion_matrix"]["stolen_phone"] == {"stolen_phone": 1, "invalid": 1}
    assert m["parser_level_injection_resistance"]["total"] == 0
    assert m["parser_level_injection_resistance"]["rate"] is None


def test_missing_fields_must_match_expected_nulls_in_schema_order():
    right = GOOD | {"missing_fields": [f for f in FACT_FIELDS if f not in STOLEN["expected_facts"]]}
    assert score_case(STOLEN, right, "")["missing_fields_correct"]
    assert not score_case(STOLEN, GOOD, "")["missing_fields_correct"]
    unsupported = case(expected_case_type="unsupported")
    assert score_case(unsupported, output("unsupported"), "")["missing_fields_correct"]


@pytest.mark.parametrize(
    ("predicted", "downgraded"),
    [("uncertain_phone_loss", True), ("lost_phone", True), ("stolen_phone", False), ("unsupported", False)],
)
def test_stolen_cases_downgraded_to_lost_or_uncertain(predicted, downgraded):
    assert score_case(STOLEN, output(predicted), "")["stolen_downgraded"] is downgraded


def test_language_breakdown_and_misclassified_list():
    spanish = case(tags=["spanish"]) | {"id": "T-2"}
    m = aggregate([
        score_case(case(tags=["english"]), output("stolen_phone"), ""),
        score_case(spanish, output("lost_phone", confidence=0.7), ""),
    ])
    assert m["by_language"]["english"]["classification_accuracy"]["count"] == 1
    assert m["by_language"]["spanish"]["classification_accuracy"]["count"] == 0
    assert "italian" not in m["by_language"]
    assert m["misclassified"] == [{"case_id": "T-2", "expected": "stolen_phone", "predicted": "lost_phone", "confidence": 0.7}]
    assert m["stolen_classified_lost_or_uncertain_ids"] == ["T-2"]
