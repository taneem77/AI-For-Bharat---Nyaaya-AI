"""
tests/test_rule_engine.py

Unit tests for SchemeValidator (all 3 rules + mutual exclusivity).
Pure unit tests — no AWS, no DB, no Bedrock.
"""
import pytest
from models import UserProfile
from rule_engine import SchemeValidator
from config import SCHEME_WIDOW_PENSION, SCHEME_DISABILITY_ALLOWANCE, SCHEME_NREGA


# ---------------------------------------------------------------------------
# Helper: build a valid widow in Maharashtra
# ---------------------------------------------------------------------------

def _mh_widow(**overrides) -> UserProfile:
    defaults = dict(
        age=52,
        income=12_000,
        marital_status="widow",
        dependents=2,
        state="Maharashtra",
        district="Pune",
        life_event="widow",
        is_rural=True,
        has_aadhaar=True,
    )
    defaults.update(overrides)
    return UserProfile(**defaults)


def _disabled_person(**overrides) -> UserProfile:
    defaults = dict(
        age=35,
        income=8_000,
        marital_status="single",
        dependents=0,
        state="Maharashtra",
        district="Nagpur",
        has_disability_cert=True,
        disability_percentage=60,
        life_event="disabled",
        is_rural=True,
        has_aadhaar=True,
    )
    defaults.update(overrides)
    return UserProfile(**defaults)


def _rural_rajasthan(**overrides) -> UserProfile:
    defaults = dict(
        age=30,
        income=15_000,
        marital_status="married",
        dependents=3,
        state="Rajasthan",
        district="Jaipur",
        life_event="none",
        is_rural=True,
        has_aadhaar=True,
    )
    defaults.update(overrides)
    return UserProfile(**defaults)


# ============================================================
# Rule 1: Widow Pension
# ============================================================

class TestWidowPension:
    def test_eligible_all_criteria_met(self):
        result = SchemeValidator.check_widow_pension(_mh_widow())
        assert result.eligible is True
        assert result.confidence == 0.94
        assert result.scheme_id == SCHEME_WIDOW_PENSION
        assert result.benefit_monthly == 600

    def test_ineligible_wrong_state(self):
        result = SchemeValidator.check_widow_pension(_mh_widow(state="Rajasthan"))
        assert result.eligible is False
        assert result.confidence == 0.0
        assert "Rajasthan" in result.reason

    def test_ineligible_not_widow(self):
        result = SchemeValidator.check_widow_pension(_mh_widow(marital_status="married"))
        assert result.eligible is False
        assert "married" in result.reason.lower()

    def test_ineligible_age_too_high(self):
        result = SchemeValidator.check_widow_pension(_mh_widow(age=61))
        assert result.eligible is False
        assert "61" in result.reason

    def test_ineligible_income_too_high(self):
        result = SchemeValidator.check_widow_pension(_mh_widow(income=20_000))
        assert result.eligible is False

    def test_ineligible_no_aadhaar(self):
        result = SchemeValidator.check_widow_pension(_mh_widow(has_aadhaar=False))
        assert result.eligible is False

    def test_boundary_age_exactly_60(self):
        result = SchemeValidator.check_widow_pension(_mh_widow(age=60))
        assert result.eligible is True

    def test_boundary_income_exactly_14999(self):
        result = SchemeValidator.check_widow_pension(_mh_widow(income=14_999))
        assert result.eligible is True

    def test_boundary_income_exactly_15000_fails(self):
        result = SchemeValidator.check_widow_pension(_mh_widow(income=15_000))
        assert result.eligible is False

    def test_required_documents_present(self):
        result = SchemeValidator.check_widow_pension(_mh_widow())
        assert "death_certificate" in result.required_documents
        assert "aadhaar" in result.required_documents


# ============================================================
# Rule 2: Disability Allowance
# ============================================================

class TestDisabilityAllowance:
    def test_eligible_all_criteria_met(self):
        result = SchemeValidator.check_disability_allowance(_disabled_person())
        assert result.eligible is True
        assert result.confidence == 0.87
        assert result.benefit_monthly == 500

    def test_ineligible_no_cert(self):
        result = SchemeValidator.check_disability_allowance(
            _disabled_person(has_disability_cert=False, disability_percentage=None)
        )
        assert result.eligible is False

    def test_ineligible_low_disability_pct(self):
        result = SchemeValidator.check_disability_allowance(
            _disabled_person(disability_percentage=39)
        )
        assert result.eligible is False
        assert "39%" in result.reason

    def test_boundary_disability_pct_exactly_40(self):
        result = SchemeValidator.check_disability_allowance(
            _disabled_person(disability_percentage=40)
        )
        assert result.eligible is True

    def test_ineligible_income_too_high(self):
        result = SchemeValidator.check_disability_allowance(
            _disabled_person(income=10_001)
        )
        assert result.eligible is False

    def test_boundary_income_exactly_9999(self):
        result = SchemeValidator.check_disability_allowance(
            _disabled_person(income=9_999)
        )
        assert result.eligible is True

    def test_works_across_all_supported_states(self):
        for state in ["Maharashtra", "Rajasthan", "Uttar Pradesh"]:
            dist = {"Maharashtra": "Pune", "Rajasthan": "Jaipur", "Uttar Pradesh": "Lucknow"}[state]
            result = SchemeValidator.check_disability_allowance(
                _disabled_person(state=state, district=dist)
            )
            assert result.eligible is True, f"Should be eligible in {state}"


# ============================================================
# Rule 3: NREGA
# ============================================================

class TestNREGA:
    def test_eligible_all_criteria_met(self):
        result = SchemeValidator.check_nrega(_rural_rajasthan())
        assert result.eligible is True
        assert result.confidence == 0.89
        assert result.benefit_onetime == 20_000

    def test_ineligible_urban(self):
        result = SchemeValidator.check_nrega(_rural_rajasthan(is_rural=False))
        assert result.eligible is False
        assert "urban" in result.reason.lower() or "non-rural" in result.reason.lower()

    def test_ineligible_age_too_high(self):
        result = SchemeValidator.check_nrega(_rural_rajasthan(age=66))
        assert result.eligible is False

    def test_boundary_age_exactly_65(self):
        result = SchemeValidator.check_nrega(_rural_rajasthan(age=65))
        assert result.eligible is True

    def test_ineligible_income_too_high(self):
        result = SchemeValidator.check_nrega(_rural_rajasthan(income=20_001))
        assert result.eligible is False

    def test_valid_in_all_pilot_states(self):
        mapping = {
            "Maharashtra": "Mumbai",
            "Rajasthan": "Jaipur",
            "Uttar Pradesh": "Lucknow",
        }
        for state, district in mapping.items():
            result = SchemeValidator.check_nrega(
                _rural_rajasthan(state=state, district=district)
            )
            assert result.eligible is True, f"Expected eligible in {state}"

    def test_required_docs_include_village_proof(self):
        result = SchemeValidator.check_nrega(_rural_rajasthan())
        assert "village_proof" in result.required_documents


# ============================================================
# Mutual Exclusivity
# ============================================================

class TestMutualExclusivity:
    def test_widow_wins_over_old_age_pension(self):
        schemes = [SCHEME_WIDOW_PENSION, "old_age_pension"]
        result = SchemeValidator.check_mutual_exclusivity(schemes)
        assert SCHEME_WIDOW_PENSION in result
        assert "old_age_pension" not in result

    def test_disability_wins_over_old_age_pension(self):
        schemes = [SCHEME_DISABILITY_ALLOWANCE, "old_age_pension"]
        result = SchemeValidator.check_mutual_exclusivity(schemes)
        assert SCHEME_DISABILITY_ALLOWANCE in result
        assert "old_age_pension" not in result

    def test_no_conflict_preserved(self):
        schemes = [SCHEME_WIDOW_PENSION, SCHEME_NREGA]
        result = SchemeValidator.check_mutual_exclusivity(schemes)
        assert len(result) == 2

    def test_empty_input(self):
        assert SchemeValidator.check_mutual_exclusivity([]) == []

    def test_single_scheme_unchanged(self):
        schemes = [SCHEME_WIDOW_PENSION]
        assert SchemeValidator.check_mutual_exclusivity(schemes) == [SCHEME_WIDOW_PENSION]

    def test_pure_function_does_not_mutate_input(self):
        original = [SCHEME_WIDOW_PENSION, "old_age_pension"]
        original_copy = original.copy()
        SchemeValidator.check_mutual_exclusivity(original)
        assert original == original_copy   # input unchanged


# ============================================================
# SchemeValidator dispatcher
# ============================================================

class TestDispatcher:
    def test_validate_routes_correctly(self):
        profile = _mh_widow()
        r = SchemeValidator.validate(SCHEME_WIDOW_PENSION, profile)
        assert r.scheme_id == SCHEME_WIDOW_PENSION

    def test_validate_unknown_scheme_raises(self):
        with pytest.raises(ValueError, match="Unknown scheme_id"):
            SchemeValidator.validate("nonexistent_scheme", _mh_widow())

    def test_evaluate_all_returns_all_schemes(self):
        all_results = SchemeValidator.evaluate_all(_mh_widow())
        scheme_ids = {r.scheme_id for r in all_results}
        assert SCHEME_WIDOW_PENSION in scheme_ids
        assert SCHEME_DISABILITY_ALLOWANCE in scheme_ids
        assert SCHEME_NREGA in scheme_ids

    def test_evaluate_all_widow_eligible(self):
        all_results = SchemeValidator.evaluate_all(_mh_widow())
        eligible = {r.scheme_id for r in all_results if r.eligible}
        assert SCHEME_WIDOW_PENSION in eligible
        # widow profile → not disabled, so disability_allowance should be ineligible
        assert SCHEME_DISABILITY_ALLOWANCE not in eligible
