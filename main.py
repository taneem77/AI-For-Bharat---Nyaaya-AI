"""
main.py — FastAPI application + AWS Lambda handler for Nyaaya.ai

Endpoints:
  POST /interview  — Hinglish interview, Bedrock-powered
  POST /evaluate   — Direct profile evaluation + strategy
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from pydantic import ValidationError

from bedrock_client import conduct_interview
from config import (
    SCHEME_DISABILITY_ALLOWANCE,
    SCHEME_NREGA,
    SCHEME_WIDOW_PENSION,
    logger,
)
from dynamodb_utils import (
    DynamoDBInterface,
    MockDynamoDBClient,
    RealDynamoDBClient,
    load_interview_state,
    save_interview_state,
)
from models import (
    ErrorResponse,
    EvaluateResponse,
    InterviewRequest,
    InterviewResponse,
    InterviewState,
    UserProfile,
)
from optimizer import build_summary, generate_strategy
from rule_engine import SchemeValidator

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Nyaaya.ai Eligibility API",
    description="Welfare eligibility engine: interview → extract → evaluate → strategy",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins (restrict in production via AWS WAF / API Gateway)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# DynamoDB: use mock locally, real on Lambda
# ---------------------------------------------------------------------------

def _get_db() -> DynamoDBInterface:
    """Return the appropriate DB client based on environment."""
    if os.getenv("AWS_EXECUTION_ENV") or os.getenv("USE_REAL_DYNAMODB"):
        return RealDynamoDBClient()
    return MockDynamoDBClient()


# Module-level singleton (shared across Lambda warm invocations)
_db: DynamoDBInterface = _get_db()

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    errors = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="Validation failed",
            errors=errors,
            code="VALIDATION_ERROR",
        ).model_dump(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=str(exc),
            code="BUSINESS_LOGIC_ERROR",
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled %s on %s %s: %s",
        type(exc).__name__,
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error. Please try again.",
            code="INTERNAL_ERROR",
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# POST /interview
# ---------------------------------------------------------------------------

@app.post(
    "/interview",
    response_model=InterviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Continue a Hinglish interview session",
)
async def interview_endpoint(request: InterviewRequest) -> Any:
    """
    Multi-turn interview powered by Bedrock.

    - Loads existing session from DynamoDB (or creates fresh state)
    - Calls Claude 3.5 Sonnet with conversation context
    - Merges extracted data into running profile (partial updates)
    - Persists state back to DynamoDB
    - Returns the next question and partial extracted data
    """

    # 1. Load or initialise session
    state = load_interview_state(request.session_id, _db)
    if state is None:
        logger.info("New session: %s", request.session_id)
        state = InterviewState(user_id=request.session_id)

    # Safety: cap runaway conversations
    if state.interview_complete:
        return InterviewResponse(
            turn=state.turn_count,
            next_question=(
                "Aapka interview pehle se complete ho chuka hai. "
                "Evaluation ke liye /evaluate call karein."
            ),
            extracted_so_far=(
                state.extracted_profile.model_dump(mode="json")
                if state.extracted_profile
                else {}
            ),
            interview_complete=True,
        )

    # 2. Call Bedrock
    history_dicts = [
        {
            "turn": t.turn,
            "user_input": t.user_input,
            "assistant_response": t.assistant_response,
        }
        for t in state.conversation_history
    ]
    bedrock_result = conduct_interview(request.user_input, history_dicts)

    next_question: str = bedrock_result.get(
        "next_question", "Kya aap thoda aur detail de sakte hain?"
    )
    extracted_data: dict[str, Any] = bedrock_result.get("extracted_data", {})
    interview_complete: bool = bedrock_result.get("interview_complete", False)

    # 3. Merge extracted data into stored profile (partial updates)
    #    Priority order: validated profile → last turn's extracted_so_far → new Bedrock data
    merged_fields: dict[str, Any] = {}

    # Seed from validated profile if one exists
    if state.extracted_profile:
        merged_fields = state.extracted_profile.model_dump(mode="json")
    # Fallback: accumulate from last turn's extracted_so_far (pre-profile-build)
    elif state.conversation_history:
        merged_fields = dict(state.conversation_history[-1].extracted_so_far)

    # Merge in the new extractions from this turn (non-None values win)
    merged_fields.update({k: v for k, v in extracted_data.items() if v is not None})


    # Attempt Pydantic parse (only when we have the minimum required fields)
    required_for_profile = {"age", "income", "marital_status", "dependents", "state", "district"}
    new_profile: UserProfile | None = state.extracted_profile

    if required_for_profile.issubset(merged_fields.keys()):
        try:
            new_profile = UserProfile(**merged_fields)
        except ValidationError as exc:
            logger.warning("Partial profile validation error (re-asking): %s", exc)
            interview_complete = False  # force continuation to fix bad data

    # 4. Update state
    state.add_turn(
        user_input=request.user_input,
        assistant_response=next_question,
        extracted_data=merged_fields,
    )
    state.extracted_profile = new_profile
    state.interview_complete = interview_complete

    # 5. Persist
    save_interview_state(request.session_id, state, _db)

    return InterviewResponse(
        turn=state.turn_count,
        next_question=next_question,
        extracted_so_far=merged_fields,
        interview_complete=interview_complete,
    )


# ---------------------------------------------------------------------------
# POST /evaluate
# ---------------------------------------------------------------------------

@app.post(
    "/evaluate",
    response_model=EvaluateResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate welfare eligibility for a given profile",
)
async def evaluate_endpoint(profile: UserProfile) -> Any:
    """
    3-layer validation pipeline:
    1. Pydantic (auto) — type + range + cross-field
    2. Rule engine    — deterministic per-scheme checks
    3. Strategy       — ranked application timeline

    Returns full eligibility results + strategy + summary.
    """

    # Layer 2+3: rule engine (Layer 1 happens automatically via Pydantic)
    all_results = SchemeValidator.evaluate_all(profile)

    eligible_results = [r for r in all_results if r.eligible]
    eligible_ids = [r.scheme_id for r in eligible_results]

    # Generate strategy
    strategy = generate_strategy(eligible_ids, eligible_results)

    # Build summary
    summary = build_summary(all_results, strategy)

    return EvaluateResponse(
        eligible_schemes=all_results,      # include ineligible for transparency
        strategy=strategy,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "service": "Nyaaya.ai Eligibility API",
        "version": "1.0.0",
        "status": "ok",
        "endpoints": [
            {"method": "POST", "path": "/interview", "description": "Multi-turn Hinglish interview (Bedrock)"},
            {"method": "POST", "path": "/evaluate",  "description": "Direct profile eligibility evaluation"},
            {"method": "GET",  "path": "/health",    "description": "Health check"},
            {"method": "GET",  "path": "/docs",      "description": "Swagger UI"},
            {"method": "GET",  "path": "/redoc",     "description": "ReDoc API docs"},
        ],
        "quick_start": {
            "interview": "POST /interview  {user_input, session_id}",
            "evaluate":  "POST /evaluate   {age, income, marital_status, ...}",
        },
    }


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# AWS Lambda handler (Mangum)
# ---------------------------------------------------------------------------

handler = Mangum(app, lifespan="off")
