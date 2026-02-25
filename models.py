"""
models.py — Pydantic v2 strict schemas for Nyaaya.ai
Covers: UserProfile, InterviewState, EligibilityResult, StrategyStep
"""
from __future__ import annotations

import time
import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, model_validator, field_validator

from config import (
    INCOME_WARNING_THRESHOLD,
    SESSION_TTL_SECONDS,
    MaritalStatus,
    LifeEvent,
    STATE_ALIASES,
    logger,
)

# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    """Structured user eligibility data extracted from interview."""

    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    age: int = Field(..., ge=18, le=120, description="User's age in years")
    income: int = Field(..., ge=0, le=1_000_000, description="Annual income in INR")
    marital_status: MaritalStatus
    dependents: int = Field(..., ge=0, le=20, description="Number of dependents")
    state: str = Field(..., description="State (Maharashtra / Rajasthan / Uttar Pradesh)")
    district: str = Field(..., min_length=1, description="District name")
    has_disability_cert: bool = Field(default=False)
    disability_percentage: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Percentage disability — required when has_disability_cert=True",
    )
    life_event: LifeEvent = Field(default=LifeEvent.NONE)
    is_rural: bool = Field(default=True)
    has_aadhaar: bool = Field(default=True)

    # ------------------------------------------------------------------
    # Field-level validators
    # ------------------------------------------------------------------

    @field_validator("state", mode="before")
    @classmethod
    def normalise_state(cls, v: str) -> str:
        """Case-insensitive normalisation; reject unsupported states."""
        normalised = STATE_ALIASES.get(v.strip().lower())
        if normalised is None:
            raise ValueError(
                f"state '{v}' is not supported. Supported: Maharashtra, Rajasthan, Uttar Pradesh"
            )
        return normalised

    @field_validator("income", mode="after")
    @classmethod
    def warn_high_income(cls, v: int) -> int:
        if v > INCOME_WARNING_THRESHOLD:
            logger.warning("Possible data-entry error: income=%d exceeds ₹10L", v)
        return v

    # ------------------------------------------------------------------
    # Cross-field validators
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def validate_business_rules(self) -> "UserProfile":
        # Rule: ELDERLY life_event requires age >= 60 (not < 18 is already checked)
        if self.life_event == LifeEvent.ELDERLY and self.age < 60:
            raise ValueError(
                f"life_event=ELDERLY is inconsistent with age={self.age}. "
                "Minimum age for ELDERLY is 60."
            )

        # Rule: disability cert requires percentage
        if self.has_disability_cert and self.disability_percentage is None:
            raise ValueError(
                "disability_percentage is required when has_disability_cert=True"
            )

        # Rule: disability percentage should not be set without cert
        if not self.has_disability_cert and self.disability_percentage is not None:
            logger.warning(
                "disability_percentage set but has_disability_cert=False — ignoring percentage"
            )
            # Coerce rather than error (lenient)
            object.__setattr__(self, "disability_percentage", None)

        return self


# ---------------------------------------------------------------------------
# InterviewState
# ---------------------------------------------------------------------------

class ConversationTurn(BaseModel):
    """Single turn in the interview conversation."""

    turn: int
    user_input: str
    assistant_response: str
    extracted_so_far: dict[str, Any] = Field(default_factory=dict)


class InterviewState(BaseModel):
    """Persisted interview session state (stored in DynamoDB)."""

    model_config = {"arbitrary_types_allowed": True}

    user_id: str = Field(..., description="Session or user identifier")
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    extracted_profile: UserProfile | None = Field(default=None)
    interview_complete: bool = Field(default=False)
    turn_count: int = Field(default=0)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    ttl: int = Field(
        default_factory=lambda: int(time.time()) + SESSION_TTL_SECONDS
    )

    def add_turn(
        self,
        user_input: str,
        assistant_response: str,
        extracted_data: dict[str, Any],
    ) -> None:
        """Append a turn and auto-increment counter."""
        self.turn_count += 1
        self.conversation_history.append(
            ConversationTurn(
                turn=self.turn_count,
                user_input=user_input,
                assistant_response=assistant_response,
                extracted_so_far=extracted_data,
            )
        )


# ---------------------------------------------------------------------------
# EligibilityResult
# ---------------------------------------------------------------------------

class EligibilityResult(BaseModel):
    """Outcome of a single scheme eligibility check."""

    scheme_id: str
    scheme_name: str
    eligible: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    benefit_monthly: int = Field(default=0, ge=0)
    benefit_onetime: int = Field(default=0, ge=0)
    required_documents: list[str] = Field(default_factory=list)
    processing_weeks: int = Field(..., ge=1)
    approval_rate: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# StrategyStep
# ---------------------------------------------------------------------------

class StrategyStep(BaseModel):
    """One step in the optimised application strategy timeline."""

    rank: int = Field(..., ge=1)
    scheme_id: str
    apply_week: int = Field(..., ge=1, le=52)
    reasoning: str
    total_benefit: int = Field(..., ge=0)
    timeline_weeks: int = Field(..., ge=1)


# ---------------------------------------------------------------------------
# API Request / Response models
# ---------------------------------------------------------------------------

class InterviewRequest(BaseModel):
    """Request body for POST /interview."""

    user_input: str = Field(..., min_length=1, description="User's Hinglish input")
    session_id: str = Field(..., min_length=1, description="Unique session identifier")


class InterviewResponse(BaseModel):
    """Response for POST /interview (non-error)."""

    status: str = "success"
    turn: int
    next_question: str
    extracted_so_far: dict[str, Any]
    interview_complete: bool


class EvaluateResponse(BaseModel):
    """Response for POST /evaluate (non-error)."""

    status: str = "success"
    eligible_schemes: list[EligibilityResult]
    strategy: list[StrategyStep]
    summary: dict[str, Any]


class ErrorResponse(BaseModel):
    """Standardised error response."""

    status: str = "error"
    error: str
    errors: list[dict[str, str]] = Field(default_factory=list)
    code: str
