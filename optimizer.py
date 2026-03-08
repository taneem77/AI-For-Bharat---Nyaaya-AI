"""
optimizer.py — Strategy optimizer for Nyaaya.ai

Ranks eligible schemes, groups them into application timeline phases,
and resolves mutual exclusivity before generating the final strategy.
"""
from __future__ import annotations

import logging
from config import logger
from models import EligibilityResult, StrategyStep

# ---------------------------------------------------------------------------
# Phase definitions (apply_week boundaries)
# ---------------------------------------------------------------------------
_PHASE_1_MAX_WEEK = 8         # fastest / builds credibility
_PHASE_2_MAX_WEEK = 12        # parallel applications
# Phase 3: week 13+ (sequential, requires prior approval)

# ---------------------------------------------------------------------------
# Score function
# ---------------------------------------------------------------------------

def _score_scheme(scheme: EligibilityResult) -> float:
    """
    Priority score: (total annual benefit × approval_rate) / processing_weeks
    Higher score → earlier rank → earlier apply_week.
    """
    annual_benefit = (scheme.benefit_monthly * 12) + scheme.benefit_onetime
    if scheme.processing_weeks == 0:
        return 0.0
    return (annual_benefit * scheme.approval_rate) / scheme.processing_weeks


# ---------------------------------------------------------------------------
# Phase assignment
# ---------------------------------------------------------------------------

def _assign_phase_week(rank: int, processing_weeks: int) -> int:
    """
    Assign an apply_week based on rank and processing time.
    Phase 1 (rank 1, fast schemes): Week 1
    Phase 2 (rank 2-3, parallel):   Based on rank offset to avoid doc conflicts
    Phase 3 (rank 4+, heavy):       Sequential, starts after Phase 1 completes
    """
    if rank == 1:
        return 1
    elif rank == 2:
        # Start parallel — small offset so doc collection doesn't clash
        return 4 if processing_weeks <= _PHASE_1_MAX_WEEK else 1
    elif rank == 3:
        return 8 if processing_weeks <= _PHASE_2_MAX_WEEK else 4
    else:
        # Sequential — start after previous expected approval
        return 12 + (rank - 4) * 4


# ---------------------------------------------------------------------------
# Reasoning templating
# ---------------------------------------------------------------------------

def _build_reasoning(rank: int, scheme: EligibilityResult, apply_week: int) -> str:
    parts: list[str] = []

    if apply_week <= 4:
        parts.append(f"Quick approval ({scheme.processing_weeks} weeks). Builds credibility for subsequent schemes.")
    elif apply_week <= 8:
        parts.append(f"Parallel application (apply week {apply_week}). Avoids document collection conflicts.")
    else:
        parts.append(f"Sequential application. Start after earlier schemes are approved.")

    monthly = scheme.benefit_monthly
    onetime = scheme.benefit_onetime
    if monthly > 0:
        parts.append(f"Monthly benefit: ₹{monthly}/month (₹{monthly * 12}/year).")
    if onetime > 0:
        parts.append(f"One-time benefit: ₹{onetime}.")

    parts.append(f"Approval rate: {scheme.approval_rate * 100:.0f}% (historical).")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main optimizer function
# ---------------------------------------------------------------------------

def generate_strategy(
    eligible_scheme_ids: list[str],
    eligible_results: list[EligibilityResult],
) -> list[StrategyStep]:
    """
    Generate an optimised week-by-week application strategy.

    Args:
        eligible_scheme_ids: List of scheme_ids that passed rule engine.
        eligible_results:    Full EligibilityResult objects (for benefit data).

    Returns:
        Sorted list of StrategyStep ordered by rank (ascending).
    """
    if not eligible_scheme_ids:
        logger.info("No eligible schemes — empty strategy returned")
        return []

    # Build lookup: scheme_id → EligibilityResult
    result_map: dict[str, EligibilityResult] = {r.scheme_id: r for r in eligible_results}

    # Filter to eligible only and score
    scored: list[tuple[float, EligibilityResult]] = []
    for sid in eligible_scheme_ids:
        if sid in result_map:
            r = result_map[sid]
            scored.append((_score_scheme(r), r))

    # Sort descending by score
    scored.sort(key=lambda t: t[0], reverse=True)

    steps: list[StrategyStep] = []
    for rank, (score, scheme) in enumerate(scored, start=1):
        apply_week = _assign_phase_week(rank, scheme.processing_weeks)
        total_benefit = (scheme.benefit_monthly * 12) + scheme.benefit_onetime

        steps.append(
            StrategyStep(
                rank=rank,
                scheme_id=scheme.scheme_id,
                apply_week=apply_week,
                reasoning=_build_reasoning(rank, scheme, apply_week),
                total_benefit=total_benefit,
                timeline_weeks=scheme.processing_weeks,
            )
        )

    logger.info(
        "Strategy generated: %d steps | ranks=%s",
        len(steps),
        [s.scheme_id for s in steps],
    )
    return steps


# ---------------------------------------------------------------------------
# Summary builder (used in /evaluate response)
# ---------------------------------------------------------------------------

def build_summary(
    eligible_results: list[EligibilityResult],
    strategy: list[StrategyStep],
) -> dict:
    """Build the top-level summary block for the /evaluate response."""
    eligible_only = [r for r in eligible_results if r.eligible]

    total_monthly = sum(r.benefit_monthly for r in eligible_only)
    first_year_total = sum(
        (r.benefit_monthly * 12) + r.benefit_onetime for r in eligible_only
    )

    # Unique documents across all eligible schemes
    all_docs: list[str] = []
    seen: set[str] = set()
    for r in eligible_only:
        for doc in r.required_documents:
            if doc not in seen:
                all_docs.append(doc)
                seen.add(doc)

    # Longest processing pipeline
    max_timeline = (
        max((r.processing_weeks for r in eligible_only), default=0)
        if eligible_only
        else 0
    )

    return {
        "total_monthly_benefit": total_monthly,
        "first_year_total": first_year_total,
        "documents_to_obtain": all_docs,
        "estimated_total_timeline_weeks": max_timeline,
        "schemes_count": len(eligible_only),
        "nyaaya_score": compute_nyaaya_score(eligible_results, strategy),
    }


# ---------------------------------------------------------------------------
# Nyaaya Score — a 0-100 "welfare accessibility" index
# ---------------------------------------------------------------------------

def compute_nyaaya_score(
    all_results: list[EligibilityResult],
    strategy: list[StrategyStep],
) -> dict:
    """
    Compute a composite Nyaaya Score (0-100) that quantifies
    how well-served the user is by available welfare schemes.

    Components:
    - Coverage (40%):  % of schemes the user qualifies for
    - Benefit (30%):   total annual benefit as % of a ₹72,000 baseline
    - Speed (15%):     inverse of avg processing time
    - Confidence (15%): avg confidence across eligible schemes
    """
    eligible = [r for r in all_results if r.eligible]
    total = len(all_results) if all_results else 1

    # Coverage: what % of available schemes they qualify for
    coverage = (len(eligible) / total) * 100

    # Benefit: annual benefit as % of ₹72,000 baseline (avg rural family income)
    annual = sum((r.benefit_monthly * 12) + r.benefit_onetime for r in eligible)
    benefit = min((annual / 72_000) * 100, 100)

    # Speed: inverse of average processing time (faster = higher score)
    if eligible:
        avg_weeks = sum(r.processing_weeks for r in eligible) / len(eligible)
        speed = max(100 - (avg_weeks * 5), 0)  # 20 weeks = 0, 0 weeks = 100
    else:
        speed = 0

    # Confidence: average confidence of eligible schemes
    confidence = (sum(r.confidence for r in eligible) / len(eligible) * 100) if eligible else 0

    # Weighted composite
    score = round(
        coverage * 0.40
        + benefit * 0.30
        + speed * 0.15
        + confidence * 0.15,
        1,
    )

    return {
        "score": min(score, 100),
        "grade": _score_grade(score),
        "breakdown": {
            "coverage": round(coverage, 1),
            "benefit": round(benefit, 1),
            "speed": round(speed, 1),
            "confidence": round(confidence, 1),
        },
        "interpretation": _score_interpretation(score),
    }


def _score_grade(score: float) -> str:
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    elif score >= 20:
        return "D"
    return "F"


def _score_interpretation(score: float) -> str:
    if score >= 80:
        return "Excellent coverage! You qualify for multiple schemes with strong benefits."
    elif score >= 60:
        return "Good coverage. You have meaningful welfare support available."
    elif score >= 40:
        return "Moderate coverage. Some schemes apply, but gaps exist."
    elif score >= 20:
        return "Limited coverage. Few schemes match your profile currently."
    return "Very limited options. Consider checking if your profile details are complete."
