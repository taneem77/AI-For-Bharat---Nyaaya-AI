"""
rule_engine.py — Dynamic deterministic eligibility rule engine for Nyaaya.ai

Reads scheme definitions from scheme_registry.py and evaluates eligibility
using operator-based rules. Adding a new scheme = adding a registry entry.
Zero code changes needed.

Supported operators: ==, !=, >, <, >=, <=, in, not_in, exists, between
"""
from __future__ import annotations

from typing import Any

from config import logger
from models import EligibilityResult, UserProfile
from scheme_registry import (
    SCHEME_REGISTRY,
    MUTUAL_EXCLUSIONS,
    get_schemes_for_state,
)


# ---------------------------------------------------------------------------
# Operator evaluation
# ---------------------------------------------------------------------------

def _eval_rule(field_value: Any, op: str, rule_value: Any) -> bool:
    """Evaluate a single rule condition."""
    if field_value is None:
        if op == "exists":
            return False
        return False

    if op == "==":
        if isinstance(field_value, str) and isinstance(rule_value, str):
            return field_value.lower() == rule_value.lower()
        return field_value == rule_value
    elif op == "!=":
        if isinstance(field_value, str) and isinstance(rule_value, str):
            return field_value.lower() != rule_value.lower()
        return field_value != rule_value
    elif op == ">":
        return field_value > rule_value
    elif op == "<":
        return field_value < rule_value
    elif op == ">=":
        return field_value >= rule_value
    elif op == "<=":
        return field_value <= rule_value
    elif op == "in":
        if isinstance(field_value, str):
            return field_value.lower() in [v.lower() if isinstance(v, str) else v for v in rule_value]
        return field_value in rule_value
    elif op == "not_in":
        if isinstance(field_value, str):
            return field_value.lower() not in [v.lower() if isinstance(v, str) else v for v in rule_value]
        return field_value not in rule_value
    elif op == "exists":
        return field_value is not None
    elif op == "between":
        low, high = rule_value
        return low <= field_value <= high
    else:
        logger.warning("Unknown operator: %s", op)
        return False


def _get_field_value(profile: UserProfile, field: str) -> Any:
    """Extract field value from profile, handling enum types."""
    val = getattr(profile, field, None)
    if val is None:
        return None
    if hasattr(val, "value"):
        return val.value
    return val


def _describe_rule(field: str, op: str, value: Any, passed: bool, actual: Any = None) -> str:
    """Generate human-readable description of a rule check."""
    field_display = field.replace("_", " ")
    actual_str = str(actual) if actual is not None else ""

    # Special handling for well-known boolean fields
    if field == "is_rural" and op == "==" and value is True:
        return "rural resident" if passed else "non-rural (urban) residents are not eligible"
    if field == "has_aadhaar" and op == "==" and value is True:
        return "has Aadhaar card" if passed else "does not have Aadhaar card"
    if field == "has_disability_cert" and op == "==" and value is True:
        return "has valid disability certificate" if passed else "no disability certificate found"

    if op == "==" and passed:
        return f"{field_display} is {actual_str}" if actual_str else f"{field_display} matches requirement"
    elif op == "==" and not passed:
        return f"{field_display} is {actual_str} (must be {value})" if actual_str else f"{field_display} does not match (needs {value})"
    elif op == "between":
        if passed:
            return f"{field_display} {actual_str} is between {value[0]}-{value[1]}"
        return f"{field_display} {actual_str} is outside allowed range ({value[0]}-{value[1]})"
    elif op == "<":
        rupee = "\u20B9"
        if field == "income":
            if passed:
                return f"income {rupee}{actual} is below {rupee}{value} threshold"
            return f"income {rupee}{actual} exceeds {rupee}{value} limit"
        if passed:
            return f"{field_display} {actual_str} below {value} threshold"
        return f"{field_display} {actual_str} exceeds {value} limit"
    elif op == ">=":
        if field == "disability_percentage":
            if passed:
                return f"disability percentage {actual}% meets >=  {value}% requirement"
            return f"disability percentage {actual}% is below {value}% threshold"
        if passed:
            return f"{field_display} {actual_str} meets minimum {value}"
        return f"{field_display} {actual_str} is below {value}"
    elif op == ">":
        return f"{field_display} {actual_str} {'above' if passed else 'at or below'} {value}"
    elif op == "in":
        return f"{field_display} {'matches' if passed else 'does not match'} required values"
    elif op == "not_in":
        return f"{field_display} check {'passed' if passed else 'failed'}"
    elif op == "<=":
        return f"{field_display} {'at or below' if passed else 'above'} {value}"
    elif op == "!=":
        return f"{field_display} check {'passed' if passed else 'failed'}"
    elif op == "exists":
        return f"{field_display} {'provided' if passed else 'missing'}"
    else:
        return f"{field_display} check {'passed' if passed else 'failed'}"


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate_scheme(scheme: dict[str, Any], profile: UserProfile) -> EligibilityResult:
    """Evaluate a single scheme against a user profile using its rules."""
    reasons: list[str] = []
    failed: list[str] = []

    for rule in scheme["rules"]:
        field = rule["field"]
        op = rule["op"]
        value = rule["value"]

        field_value = _get_field_value(profile, field)
        passed = _eval_rule(field_value, op, value)
        desc = _describe_rule(field, op, value, passed, actual=field_value)

        if passed:
            reasons.append(desc)
        else:
            failed.append(desc)

    eligible = len(failed) == 0

    if eligible:
        reason = "You meet all eligibility criteria: " + ", ".join(reasons)
        confidence = scheme.get("confidence", 0.85)
    else:
        reason = "Not eligible: " + "; ".join(failed)
        confidence = 0.0

    logger.info(
        "evaluate_scheme | %s | eligible=%s | profile.state=%s",
        scheme["id"], eligible, profile.state,
    )

    return EligibilityResult(
        scheme_id=scheme["id"],
        scheme_name=scheme["name_en"],
        eligible=eligible,
        confidence=confidence,
        reason=reason,
        benefit_monthly=scheme.get("benefit_monthly", 0),
        benefit_onetime=scheme.get("benefit_onetime", 0),
        required_documents=scheme.get("required_documents", []),
        processing_weeks=scheme.get("processing_weeks", 8),
        approval_rate=scheme.get("approval_rate", 0.80),
    )


# ---------------------------------------------------------------------------
# SchemeValidator — backward-compatible class interface
# ---------------------------------------------------------------------------

class SchemeValidator:
    """
    Deterministic eligibility rule engine.
    Now powered by the dynamic scheme registry.
    """

    @staticmethod
    def validate(scheme_id: str, profile: UserProfile) -> EligibilityResult:
        """Evaluate a single scheme by ID."""
        for scheme in SCHEME_REGISTRY:
            if scheme["id"] == scheme_id:
                return evaluate_scheme(scheme, profile)
        raise ValueError(f"Unknown scheme_id: '{scheme_id}'")

    @staticmethod
    def check_mutual_exclusivity(eligible_schemes: list[str]) -> list[str]:
        """Remove conflicting scheme(s), keeping the higher-benefit winner."""
        result = list(eligible_schemes)
        for (scheme1, scheme2), winner in MUTUAL_EXCLUSIONS.items():
            if scheme1 in result and scheme2 in result:
                loser = scheme2 if winner == scheme1 else scheme1
                result.remove(loser)
                logger.info(
                    "Mutual exclusivity: removed '%s' in favour of '%s'",
                    loser, winner,
                )
        return result

    @staticmethod
    def evaluate_all(profile: UserProfile) -> list[EligibilityResult]:
        """
        Run every applicable scheme for the user's state,
        apply mutual exclusivity, and return all results.
        """
        applicable_schemes = get_schemes_for_state(profile.state)

        results: dict[str, EligibilityResult] = {}
        for scheme in applicable_schemes:
            results[scheme["id"]] = evaluate_scheme(scheme, profile)

        eligible_ids = [sid for sid, r in results.items() if r.eligible]
        resolved_ids = SchemeValidator.check_mutual_exclusivity(eligible_ids)

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

    # Backward-compatible individual check methods
    @staticmethod
    def check_widow_pension(profile: UserProfile) -> EligibilityResult:
        return SchemeValidator.validate("widow_pension_mh", profile)

    @staticmethod
    def check_disability_allowance(profile: UserProfile) -> EligibilityResult:
        return SchemeValidator.validate("disability_allowance", profile)

    @staticmethod
    def check_nrega(profile: UserProfile) -> EligibilityResult:
        return SchemeValidator.validate("nrega", profile)

    @staticmethod
    def check_pm_kisan(profile: UserProfile) -> EligibilityResult:
        return SchemeValidator.validate("pm_kisan", profile)

    @staticmethod
    def check_old_age_pension(profile: UserProfile) -> EligibilityResult:
        return SchemeValidator.validate("old_age_pension", profile)

    @staticmethod
    def check_ujjwala(profile: UserProfile) -> EligibilityResult:
        return SchemeValidator.validate("ujjwala_yojana", profile)
