"""
rule_engine.py — Deterministic eligibility rule engine for Nyaaya.ai

All methods are @staticmethod pure functions with ZERO side effects.
Same input always produces same output.
"""
from __future__ import annotations

import logging
from typing import Callable

from config import (
    SCHEME_DISABILITY_ALLOWANCE,
    SCHEME_NREGA,
    SCHEME_OLD_AGE_PENSION,
    SCHEME_PM_KISAN,
    SCHEME_UJJWALA,
    SCHEME_WIDOW_PENSION,
    MaritalStatus,
    LifeEvent,
    logger,
)
from models import EligibilityResult, UserProfile

# ---------------------------------------------------------------------------
# Internal scheme metadata registry
# ---------------------------------------------------------------------------

_SCHEME_META: dict[str, dict] = {
    SCHEME_WIDOW_PENSION: {
        "scheme_name": "Widow Pension Scheme",
        "benefit_monthly": 600,
        "benefit_onetime": 0,
        "required_documents": [
            "death_certificate",
            "aadhaar",
            "income_certificate",
            "bank_passbook",
        ],
        "processing_weeks": 8,
        "approval_rate": 0.91,
    },
    SCHEME_DISABILITY_ALLOWANCE: {
        "scheme_name": "Disability Allowance",
        "benefit_monthly": 500,
        "benefit_onetime": 0,
        "required_documents": [
            "disability_cert",
            "aadhaar",
            "income_certificate",
        ],
        "processing_weeks": 6,
        "approval_rate": 0.85,
    },
    SCHEME_NREGA: {
        "scheme_name": "NREGA Employment Guarantee",
        "benefit_monthly": 0,
        "benefit_onetime": 20_000,          # ₹200/day × 100 days
        "required_documents": [
            "aadhaar",
            "village_proof",
            "employment_card_application",
        ],
        "processing_weeks": 12,
        "approval_rate": 0.78,
    },
    SCHEME_PM_KISAN: {
        "scheme_name": "PM-KISAN Samman Nidhi",
        "benefit_monthly": 500,             # ₹6,000/year = ₹500/month
        "benefit_onetime": 0,
        "required_documents": [
            "aadhaar",
            "land_ownership_record",
            "bank_passbook",
            "kisan_registration",
        ],
        "processing_weeks": 6,
        "approval_rate": 0.92,
    },
    SCHEME_OLD_AGE_PENSION: {
        "scheme_name": "Indira Gandhi Old Age Pension",
        "benefit_monthly": 500,
        "benefit_onetime": 0,
        "required_documents": [
            "aadhaar",
            "age_proof",
            "bpl_card",
            "bank_passbook",
        ],
        "processing_weeks": 10,
        "approval_rate": 0.88,
    },
    SCHEME_UJJWALA: {
        "scheme_name": "PM Ujjwala Yojana (Free LPG)",
        "benefit_monthly": 0,
        "benefit_onetime": 1_600,           # free LPG connection subsidy
        "required_documents": [
            "aadhaar",
            "bpl_card",
            "bank_passbook",
            "address_proof",
        ],
        "processing_weeks": 4,
        "approval_rate": 0.94,
    },
}

# ---------------------------------------------------------------------------
# Mutual exclusivity rules
# (pair) → scheme_id to KEEP (the one with higher benefit)
# ---------------------------------------------------------------------------

_MUTUAL_EXCLUSIONS: dict[tuple[str, str], str] = {
    (SCHEME_WIDOW_PENSION, SCHEME_OLD_AGE_PENSION): SCHEME_WIDOW_PENSION,
    (SCHEME_DISABILITY_ALLOWANCE, SCHEME_OLD_AGE_PENSION): SCHEME_DISABILITY_ALLOWANCE,
}


# ---------------------------------------------------------------------------
# Helper — build result object
# ---------------------------------------------------------------------------

def _make_result(
    scheme_id: str,
    eligible: bool,
    confidence: float,
    reason: str,
) -> EligibilityResult:
    meta = _SCHEME_META[scheme_id]
    return EligibilityResult(
        scheme_id=scheme_id,
        scheme_name=meta["scheme_name"],
        eligible=eligible,
        confidence=confidence,
        reason=reason,
        benefit_monthly=meta["benefit_monthly"],
        benefit_onetime=meta["benefit_onetime"],
        required_documents=meta["required_documents"],
        processing_weeks=meta["processing_weeks"],
        approval_rate=meta["approval_rate"],
    )


# ---------------------------------------------------------------------------
# SchemeValidator — main class
# ---------------------------------------------------------------------------

class SchemeValidator:
    """
    Deterministic eligibility rule engine.
    All methods are class-level static functions.
    No state. No DB calls. No side effects.
    """

    # ------------------------------------------------------------------
    # Rule 1: Widow Pension (Maharashtra only)
    # ------------------------------------------------------------------

    @staticmethod
    def check_widow_pension(profile: UserProfile) -> EligibilityResult:
        """
        Eligibility:
        - marital_status == WIDOW
        - 18 <= age <= 60
        - income < 15,000
        - state == Maharashtra
        - has_aadhaar == True
        """
        scheme_id = SCHEME_WIDOW_PENSION
        reasons: list[str] = []
        failed: list[str] = []

        checks = [
            (profile.marital_status == MaritalStatus.WIDOW,
             "marital status is widow",
             f"marital status is {profile.marital_status.value} (must be widow)"),
            (18 <= profile.age <= 60,
             f"age {profile.age} is between 18–60",
             f"age {profile.age} is outside allowed range (18–60)"),
            (profile.income < 15_000,
             f"income ₹{profile.income} is below ₹15,000 threshold",
             f"income ₹{profile.income} exceeds ₹15,000 limit"),
            (profile.state.lower() == "maharashtra",
             "resident of Maharashtra",
             f"state is {profile.state} (scheme is Maharashtra-only)"),
            (profile.has_aadhaar,
             "has Aadhaar card",
             "does not have Aadhaar card"),
        ]

        for passed, ok_reason, fail_reason in checks:
            if passed:
                reasons.append(ok_reason)
            else:
                failed.append(fail_reason)

        eligible = len(failed) == 0
        if eligible:
            reason = (
                "You meet all eligibility criteria: "
                + ", ".join(reasons)
            )
            confidence = 0.94
        else:
            reason = "Not eligible: " + "; ".join(failed)
            confidence = 0.0

        logger.info(
            "check_widow_pension | eligible=%s | profile.age=%d state=%s",
            eligible,
            profile.age,
            profile.state,
        )
        return _make_result(scheme_id, eligible, confidence, reason)

    # ------------------------------------------------------------------
    # Rule 2: Disability Allowance (all states)
    # ------------------------------------------------------------------

    @staticmethod
    def check_disability_allowance(profile: UserProfile) -> EligibilityResult:
        """
        Eligibility:
        - has_disability_cert == True
        - disability_percentage >= 40
        - income < 10,000
        - age >= 18
        """
        scheme_id = SCHEME_DISABILITY_ALLOWANCE
        reasons: list[str] = []
        failed: list[str] = []

        pct = profile.disability_percentage or 0

        checks = [
            (profile.has_disability_cert,
             "has valid disability certificate",
             "no disability certificate found"),
            (pct >= 40,
             f"disability percentage {pct}% meets ≥40% requirement",
             f"disability percentage {pct}% is below 40% threshold"),
            (profile.income < 10_000,
             f"income ₹{profile.income} is below ₹10,000 threshold",
             f"income ₹{profile.income} exceeds ₹10,000 limit"),
            (profile.age >= 18,
             f"age {profile.age} meets ≥18 requirement",
             f"age {profile.age} is below 18"),
        ]

        for passed, ok_reason, fail_reason in checks:
            if passed:
                reasons.append(ok_reason)
            else:
                failed.append(fail_reason)

        eligible = len(failed) == 0
        if eligible:
            reason = "You meet all eligibility criteria: " + ", ".join(reasons)
            confidence = 0.87
        else:
            reason = "Not eligible: " + "; ".join(failed)
            confidence = 0.0

        logger.info(
            "check_disability_allowance | eligible=%s | pct=%d income=%d",
            eligible,
            pct,
            profile.income,
        )
        return _make_result(scheme_id, eligible, confidence, reason)

    # ------------------------------------------------------------------
    # Rule 3: NREGA (rural, pilot states only)
    # ------------------------------------------------------------------

    @staticmethod
    def check_nrega(profile: UserProfile) -> EligibilityResult:
        """
        Eligibility:
        - is_rural == True
        - 18 <= age <= 65
        - state in pilot states
        - income < 20,000
        """
        scheme_id = SCHEME_NREGA
        reasons: list[str] = []
        failed: list[str] = []

        pilot_states = {"maharashtra", "rajasthan", "uttar pradesh"}

        checks = [
            (profile.is_rural,
             "rural resident",
             "non-rural (urban) residents are not eligible for NREGA"),
            (18 <= profile.age <= 65,
             f"age {profile.age} is between 18–65",
             f"age {profile.age} is outside allowed range (18–65)"),
            (profile.state.lower() in pilot_states,
             f"{profile.state} is in the NREGA pilot programme",
             f"{profile.state} is not in the current NREGA pilot states"),
            (profile.income < 20_000,
             f"income ₹{profile.income} is below ₹20,000 threshold",
             f"income ₹{profile.income} exceeds ₹20,000 limit"),
        ]

        for passed, ok_reason, fail_reason in checks:
            if passed:
                reasons.append(ok_reason)
            else:
                failed.append(fail_reason)

        eligible = len(failed) == 0
        if eligible:
            reason = "You meet all eligibility criteria: " + ", ".join(reasons)
            confidence = 0.89
        else:
            reason = "Not eligible: " + "; ".join(failed)
            confidence = 0.0

        logger.info(
            "check_nrega | eligible=%s | is_rural=%s state=%s",
            eligible,
            profile.is_rural,
            profile.state,
        )
        return _make_result(scheme_id, eligible, confidence, reason)

    # ------------------------------------------------------------------
    # Rule 4: PM-KISAN Samman Nidhi (farmers, all pilot states)
    # ------------------------------------------------------------------

    @staticmethod
    def check_pm_kisan(profile: UserProfile) -> EligibilityResult:
        scheme_id = SCHEME_PM_KISAN
        reasons: list[str] = []
        failed: list[str] = []

        checks = [
            (profile.life_event == LifeEvent.FARMER,
             "registered as farmer",
             f"life_event is {profile.life_event.value} (must be farmer)"),
            (profile.income < 200_000,
             f"income ₹{profile.income} is below ₹2,00,000 threshold",
             f"income ₹{profile.income} exceeds ₹2,00,000 limit"),
            (profile.is_rural,
             "rural resident",
             "urban residents are not eligible for PM-KISAN"),
            (profile.has_aadhaar,
             "has Aadhaar card",
             "Aadhaar card required for PM-KISAN DBT"),
        ]

        for passed, ok_reason, fail_reason in checks:
            (reasons if passed else failed).append(ok_reason if passed else fail_reason)

        eligible = len(failed) == 0
        confidence = 0.93 if eligible else 0.0
        reason = ("You meet all eligibility criteria: " + ", ".join(reasons)) if eligible else ("Not eligible: " + "; ".join(failed))

        logger.info("check_pm_kisan | eligible=%s | life_event=%s income=%d", eligible, profile.life_event.value, profile.income)
        return _make_result(scheme_id, eligible, confidence, reason)

    # ------------------------------------------------------------------
    # Rule 5: Indira Gandhi Old Age Pension
    # ------------------------------------------------------------------

    @staticmethod
    def check_old_age_pension(profile: UserProfile) -> EligibilityResult:
        scheme_id = SCHEME_OLD_AGE_PENSION
        reasons: list[str] = []
        failed: list[str] = []

        checks = [
            (profile.age >= 60,
             f"age {profile.age} meets ≥60 requirement",
             f"age {profile.age} is below 60"),
            (profile.income < 10_000,
             f"income ₹{profile.income} is below ₹10,000 BPL threshold",
             f"income ₹{profile.income} exceeds ₹10,000 BPL limit"),
            (profile.has_aadhaar,
             "has Aadhaar card",
             "Aadhaar card required"),
        ]

        for passed, ok_reason, fail_reason in checks:
            (reasons if passed else failed).append(ok_reason if passed else fail_reason)

        eligible = len(failed) == 0
        confidence = 0.90 if eligible else 0.0
        reason = ("You meet all eligibility criteria: " + ", ".join(reasons)) if eligible else ("Not eligible: " + "; ".join(failed))

        logger.info("check_old_age_pension | eligible=%s | age=%d income=%d", eligible, profile.age, profile.income)
        return _make_result(scheme_id, eligible, confidence, reason)

    # ------------------------------------------------------------------
    # Rule 6: PM Ujjwala Yojana (free LPG for BPL women)
    # ------------------------------------------------------------------

    @staticmethod
    def check_ujjwala(profile: UserProfile) -> EligibilityResult:
        scheme_id = SCHEME_UJJWALA
        reasons: list[str] = []
        failed: list[str] = []

        is_woman = profile.marital_status in {MaritalStatus.WIDOW, MaritalStatus.MARRIED, MaritalStatus.DIVORCED, MaritalStatus.SEPARATED}

        checks = [
            (is_woman,
             "eligible woman applicant",
             "PM Ujjwala prioritises women-headed households"),
            (profile.income < 15_000,
             f"income ₹{profile.income} is below BPL threshold",
             f"income ₹{profile.income} exceeds BPL threshold"),
            (profile.age >= 18,
             f"age {profile.age} meets ≥18 requirement",
             f"age {profile.age} is below 18"),
            (profile.has_aadhaar,
             "has Aadhaar card",
             "Aadhaar card required"),
        ]

        for passed, ok_reason, fail_reason in checks:
            (reasons if passed else failed).append(ok_reason if passed else fail_reason)

        eligible = len(failed) == 0
        confidence = 0.91 if eligible else 0.0
        reason = ("You meet all eligibility criteria: " + ", ".join(reasons)) if eligible else ("Not eligible: " + "; ".join(failed))

        logger.info("check_ujjwala | eligible=%s | income=%d", eligible, profile.income)
        return _make_result(scheme_id, eligible, confidence, reason)

    # ------------------------------------------------------------------
    # Dispatcher: validate by scheme_id
    # ------------------------------------------------------------------

    @staticmethod
    def validate(scheme_id: str, profile: UserProfile) -> EligibilityResult:
        """Route to the correct scheme checker by ID."""
        dispatcher: dict[str, Callable[[UserProfile], EligibilityResult]] = {
            SCHEME_WIDOW_PENSION: SchemeValidator.check_widow_pension,
            SCHEME_DISABILITY_ALLOWANCE: SchemeValidator.check_disability_allowance,
            SCHEME_NREGA: SchemeValidator.check_nrega,
            SCHEME_PM_KISAN: SchemeValidator.check_pm_kisan,
            SCHEME_OLD_AGE_PENSION: SchemeValidator.check_old_age_pension,
            SCHEME_UJJWALA: SchemeValidator.check_ujjwala,
        }
        checker = dispatcher.get(scheme_id)
        if checker is None:
            raise ValueError(f"Unknown scheme_id: '{scheme_id}'")
        return checker(profile)

    # ------------------------------------------------------------------
    # Mutual exclusivity resolver
    # ------------------------------------------------------------------

    @staticmethod
    def check_mutual_exclusivity(eligible_schemes: list[str]) -> list[str]:
        """
        Remove conflicting scheme(s), keeping the higher-benefit winner.
        Modifies a *copy* of the input list (pure function).
        """
        result = list(eligible_schemes)
        for (scheme1, scheme2), winner in _MUTUAL_EXCLUSIONS.items():
            if scheme1 in result and scheme2 in result:
                loser = scheme2 if winner == scheme1 else scheme1
                result.remove(loser)
                logger.info(
                    "Mutual exclusivity: removed '%s' in favour of '%s'",
                    loser,
                    winner,
                )
        return result

    # ------------------------------------------------------------------
    # Convenience: run ALL known schemes at once
    # ------------------------------------------------------------------

    @staticmethod
    def evaluate_all(profile: UserProfile) -> list[EligibilityResult]:
        """
        Run every scheme validator, apply mutual exclusivity, and return
        the final list (eligible + ineligible for transparency).
        """
        all_scheme_ids = [
            SCHEME_WIDOW_PENSION,
            SCHEME_DISABILITY_ALLOWANCE,
            SCHEME_NREGA,
            SCHEME_PM_KISAN,
            SCHEME_OLD_AGE_PENSION,
            SCHEME_UJJWALA,
        ]

        results: dict[str, EligibilityResult] = {
            sid: SchemeValidator.validate(sid, profile) for sid in all_scheme_ids
        }

        eligible_ids = [sid for sid, r in results.items() if r.eligible]
        resolved_ids = SchemeValidator.check_mutual_exclusivity(eligible_ids)

        # Mark ineligible schemes that were removed by mutual exclusivity
        for sid in eligible_ids:
            if sid not in resolved_ids:
                results[sid] = EligibilityResult(
                    **{
                        **results[sid].model_dump(),
                        "eligible": False,
                        "confidence": 0.0,
                        "reason": (
                            results[sid].reason
                            + " [Overridden by mutual exclusivity — higher-benefit scheme selected]"
                        ),
                    }
                )

        return list(results.values())
