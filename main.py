"""
main.py — FastAPI application + AWS Lambda handler for Nyaaya.ai

Endpoints:
  POST /interview  — Hinglish interview, Bedrock-powered
  POST /evaluate   — Direct profile evaluation + strategy
  POST /report     — PDF eligibility report
  POST /checklist  — Deduplicated document checklist
  POST /translate  — Amazon Translate
  POST /stories    — Bedrock-generated peer stories
"""
from __future__ import annotations

import io
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from mangum import Mangum
from pydantic import ValidationError

from bedrock_client import conduct_interview, generate_stories
from config import logger
from translate_client import translate_text
from dynamodb_utils import (
    DynamoDBInterface,
    MockDynamoDBClient,
    RealDynamoDBClient,
    load_interview_state,
    save_interview_state,
)
from models import (
    ChecklistItem,
    ChecklistRequest,
    ChecklistResponse,
    ErrorResponse,
    EvaluateResponse,
    FamilyEvaluateRequest,
    FamilyMember,
    InterviewRequest,
    InterviewResponse,
    InterviewState,
    ReportRequest,
    StoriesRequest,
    TranslateRequest,
    TranslateResponse,
    UserProfile,
)
from optimizer import build_summary, generate_strategy
from rule_engine import SchemeValidator
from scheme_registry import get_scheme_by_id, SCHEME_REGISTRY

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Nyaaya.ai Eligibility API",
    description="Welfare eligibility engine: interview → extract → evaluate → strategy",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

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
    if os.getenv("AWS_EXECUTION_ENV") or os.getenv("USE_REAL_DYNAMODB"):
        return RealDynamoDBClient()
    return MockDynamoDBClient()

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
        type(exc).__name__, request.method, request.url.path, str(exc),
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
    state = load_interview_state(request.session_id, _db)
    if state is None:
        logger.info("New session: %s", request.session_id)
        state = InterviewState(user_id=request.session_id)

    if state.interview_complete:
        complete_msg = (
            "Your interview is already complete. Evaluating your eligibility now."
            if request.lang == "en"
            else "Aapka interview pehle se complete ho chuka hai. Evaluation ke liye /evaluate call karein."
        )
        return InterviewResponse(
            turn=state.turn_count,
            next_question=complete_msg,
            extracted_so_far=(
                state.extracted_profile.model_dump(mode="json")
                if state.extracted_profile else {}
            ),
            interview_complete=True,
        )

    history_dicts = [
        {"turn": t.turn, "user_input": t.user_input, "assistant_response": t.assistant_response}
        for t in state.conversation_history
    ]
    accumulated: dict[str, Any] = {}
    if state.extracted_profile:
        accumulated = state.extracted_profile.model_dump(mode="json")
    elif state.conversation_history:
        accumulated = dict(state.conversation_history[-1].extracted_so_far)

    bedrock_result = conduct_interview(request.user_input, history_dicts, accumulated, lang=request.lang)

    fallback_q = "Could you tell me a bit more?" if request.lang == "en" else "Kya aap thoda aur detail de sakte hain?"
    next_question: str = bedrock_result.get("next_question", fallback_q)
    extracted_data: dict[str, Any] = bedrock_result.get("extracted_data", {})
    interview_complete: bool = bedrock_result.get("interview_complete", False)

    merged_fields: dict[str, Any] = {}
    if state.extracted_profile:
        merged_fields = state.extracted_profile.model_dump(mode="json")
    elif state.conversation_history:
        merged_fields = dict(state.conversation_history[-1].extracted_so_far)

    merged_fields.update({k: v for k, v in extracted_data.items() if v is not None})

    required_for_profile = {"age", "income", "marital_status", "dependents", "state", "district"}
    new_profile: UserProfile | None = state.extracted_profile

    if required_for_profile.issubset(merged_fields.keys()):
        try:
            new_profile = UserProfile(**merged_fields)
        except ValidationError as exc:
            logger.warning("Partial profile validation error (re-asking): %s", exc)
            interview_complete = False

    state.add_turn(
        user_input=request.user_input,
        assistant_response=next_question,
        extracted_data=merged_fields,
    )
    state.extracted_profile = new_profile
    state.interview_complete = interview_complete

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
    all_results = SchemeValidator.evaluate_all(profile)
    eligible_results = [r for r in all_results if r.eligible]
    eligible_ids = [r.scheme_id for r in eligible_results]
    strategy = generate_strategy(eligible_ids, eligible_results)
    summary = build_summary(all_results, strategy)

    return EvaluateResponse(
        eligible_schemes=all_results,
        strategy=strategy,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# POST /evaluate/family — Family Mode
# ---------------------------------------------------------------------------

@app.post(
    "/evaluate/family",
    status_code=status.HTTP_200_OK,
    summary="Evaluate welfare eligibility for primary + family members",
)
async def family_evaluate_endpoint(request: FamilyEvaluateRequest) -> Any:
    # Build primary profile
    primary_profile = UserProfile(
        age=request.age,
        income=request.income,
        marital_status=request.marital_status,
        dependents=request.dependents,
        state=request.state,
        district=request.district,
        has_disability_cert=request.has_disability_cert,
        disability_percentage=request.disability_percentage,
        life_event=request.life_event,
        is_rural=request.is_rural,
        has_aadhaar=request.has_aadhaar,
    )

    # Evaluate primary
    primary_results = SchemeValidator.evaluate_all(primary_profile)
    primary_eligible = [r for r in primary_results if r.eligible]
    primary_ids = [r.scheme_id for r in primary_eligible]
    primary_strategy = generate_strategy(primary_ids, primary_eligible)
    primary_summary = build_summary(primary_results, primary_strategy)

    members_output = []

    # Evaluate each family member
    for member in request.family_members:
        try:
            member_profile = UserProfile(
                age=max(member.age, 18),
                income=member.income,
                marital_status=member.marital_status,
                dependents=0,
                state=request.state,
                district=request.district,
                has_disability_cert=member.has_disability_cert,
                disability_percentage=member.disability_percentage,
                life_event=member.life_event,
                is_rural=request.is_rural,
                has_aadhaar=True,
            )
            member_results = SchemeValidator.evaluate_all(member_profile)
            member_eligible = [r for r in member_results if r.eligible]
            member_ids = [r.scheme_id for r in member_eligible]
            member_strategy = generate_strategy(member_ids, member_eligible)
            member_summary = build_summary(member_results, member_strategy)

            members_output.append({
                "name": member.name,
                "age": member.age,
                "eligible_schemes": member_results,
                "strategy": member_strategy,
                "summary": member_summary,
            })
        except Exception as e:
            logger.warning("Family member evaluation failed for %s: %s", member.name, e)
            members_output.append({
                "name": member.name,
                "age": member.age,
                "eligible_schemes": [],
                "strategy": [],
                "summary": {"error": str(e)},
            })

    # Deduplicate household schemes
    all_eligible_ids: set[str] = set(primary_ids)
    for m in members_output:
        for r in m.get("eligible_schemes", []):
            if hasattr(r, "eligible") and r.eligible:
                all_eligible_ids.add(r.scheme_id)
            elif isinstance(r, dict) and r.get("eligible"):
                all_eligible_ids.add(r["scheme_id"])

    # Household totals
    household_monthly = primary_summary.get("total_monthly_benefit", 0)
    household_yearly = primary_summary.get("first_year_total", 0)
    for m in members_output:
        s = m.get("summary", {})
        household_monthly += s.get("total_monthly_benefit", 0)
        household_yearly += s.get("first_year_total", 0)

    # Weighted household Nyaaya Score
    scores = [primary_summary.get("nyaaya_score", {}).get("score", 0)]
    for m in members_output:
        s = m.get("summary", {}).get("nyaaya_score", {})
        if isinstance(s, dict) and "score" in s:
            scores.append(s["score"])
    household_score = round(sum(scores) / max(len(scores), 1), 1) if scores else 0

    return {
        "status": "success",
        "primary": {
            "eligible_schemes": primary_results,
            "strategy": primary_strategy,
            "summary": primary_summary,
        },
        "family_members": members_output,
        "household_summary": {
            "total_unique_schemes": len(all_eligible_ids),
            "household_monthly_benefit": household_monthly,
            "household_annual_benefit": household_yearly,
            "household_nyaaya_score": household_score,
            "member_count": 1 + len(request.family_members),
        },
    }


# ---------------------------------------------------------------------------
# POST /checklist — Deduplicated document checklist
# ---------------------------------------------------------------------------

# Document metadata for timeline grouping and Hindi names
_DOC_META: dict[str, dict[str, Any]] = {
    "aadhaar": {"hi": "आधार कार्ड", "week": 1, "difficulty": "easy"},
    "bank_passbook": {"hi": "बैंक पासबुक", "week": 1, "difficulty": "easy"},
    "ration_card": {"hi": "राशन कार्ड", "week": 1, "difficulty": "easy"},
    "photograph": {"hi": "पासपोर्ट फ़ोटो", "week": 2, "difficulty": "easy"},
    "address_proof": {"hi": "पता प्रमाण", "week": 1, "difficulty": "easy"},
    "mobile_number": {"hi": "मोबाइल नंबर", "week": 1, "difficulty": "easy"},
    "family_photo": {"hi": "परिवार फ़ोटो", "week": 2, "difficulty": "easy"},
    "family_id_card": {"hi": "परिवार पहचान पत्र", "week": 2, "difficulty": "medium"},
    "family_card": {"hi": "परिवार कार्ड", "week": 2, "difficulty": "medium"},
    "household_proof": {"hi": "घर का प्रमाण", "week": 2, "difficulty": "medium"},
    "self_declaration": {"hi": "स्व-घोषणा पत्र", "week": 2, "difficulty": "easy"},
    "death_certificate": {"hi": "मृत्यु प्रमाण पत्र", "week": 2, "difficulty": "medium"},
    "income_certificate": {"hi": "आय प्रमाण पत्र", "week": 3, "difficulty": "medium"},
    "bpl_card": {"hi": "बीपीएल कार्ड", "week": 3, "difficulty": "hard"},
    "age_proof": {"hi": "उम्र प्रमाण", "week": 2, "difficulty": "easy"},
    "caste_certificate": {"hi": "जाति प्रमाण पत्र", "week": 3, "difficulty": "medium"},
    "disability_cert": {"hi": "विकलांगता प्रमाण पत्र", "week": 3, "difficulty": "hard"},
    "land_document": {"hi": "भूमि दस्तावेज़", "week": 4, "difficulty": "hard"},
    "land_ownership_record": {"hi": "भूमि स्वामित्व रिकॉर्ड", "week": 4, "difficulty": "hard"},
    "village_proof": {"hi": "गाँव प्रमाण", "week": 2, "difficulty": "easy"},
    "employment_card_application": {"hi": "रोज़गार कार्ड आवेदन", "week": 2, "difficulty": "easy"},
    "kisan_registration": {"hi": "किसान पंजीकरण", "week": 3, "difficulty": "medium"},
    "pregnancy_certificate": {"hi": "गर्भावस्था प्रमाण पत्र", "week": 3, "difficulty": "medium"},
    "mcp_card": {"hi": "एमसीपी कार्ड", "week": 2, "difficulty": "easy"},
    "birth_certificate_daughter": {"hi": "बेटी का जन्म प्रमाण पत्र", "week": 2, "difficulty": "easy"},
    "trade_certificate": {"hi": "व्यापार प्रमाण पत्र", "week": 3, "difficulty": "medium"},
    "business_plan": {"hi": "व्यापार योजना", "week": 3, "difficulty": "medium"},
    "college_id": {"hi": "कॉलेज आईडी", "week": 2, "difficulty": "easy"},
    "marksheet": {"hi": "मार्कशीट", "week": 2, "difficulty": "easy"},
    "samagra_id": {"hi": "समग्र आईडी", "week": 2, "difficulty": "medium"},
}


@app.post(
    "/checklist",
    response_model=ChecklistResponse,
    status_code=status.HTTP_200_OK,
    summary="Get deduplicated document checklist with timeline",
)
async def checklist_endpoint(request: ChecklistRequest) -> Any:
    doc_to_schemes: dict[str, list[str]] = {}

    for sid in request.scheme_ids:
        scheme = get_scheme_by_id(sid)
        if not scheme:
            continue
        for doc in scheme.get("required_documents", []):
            if doc not in doc_to_schemes:
                doc_to_schemes[doc] = []
            doc_to_schemes[doc].append(scheme["name_en"])

    checklist: list[ChecklistItem] = []
    for doc, schemes in sorted(doc_to_schemes.items(), key=lambda x: _DOC_META.get(x[0], {}).get("week", 4)):
        meta = _DOC_META.get(doc, {})
        checklist.append(ChecklistItem(
            document=doc.replace("_", " ").title(),
            document_hi=meta.get("hi", ""),
            needed_for=schemes,
            timeline_week=meta.get("week", 3),
            difficulty=meta.get("difficulty", "medium"),
        ))

    # Smart tips
    multi_docs = [c for c in checklist if len(c.needed_for) >= 3]
    tips = []
    for c in multi_docs[:2]:
        tips.append(f"Get your {c.document} first — it unlocks {len(c.needed_for)} schemes.")

    summary_text = f"{len(checklist)} documents needed for {len(request.scheme_ids)} schemes."
    if tips:
        summary_text += " " + " ".join(tips)

    return ChecklistResponse(
        checklist=checklist,
        total_documents=len(checklist),
        summary=summary_text,
    )


# ---------------------------------------------------------------------------
# POST /report — PDF eligibility report
# ---------------------------------------------------------------------------

@app.post(
    "/report",
    status_code=status.HTTP_200_OK,
    summary="Generate PDF eligibility report",
)
async def report_endpoint(request: ReportRequest) -> Any:
    try:
        from report_generator import generate_pdf_report
        pdf_bytes = generate_pdf_report(request.profile, request.results)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=nyaaya_report.pdf"},
        )
    except ImportError:
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={"error": "PDF generation not available. Install fpdf2."},
        )
    except Exception as e:
        logger.error("Report generation failed: %s", e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Report generation failed: {str(e)}"},
        )


# ---------------------------------------------------------------------------
# POST /translate
# ---------------------------------------------------------------------------

@app.post(
    "/translate",
    response_model=TranslateResponse,
    status_code=status.HTTP_200_OK,
    summary="Translate text between languages using Amazon Translate",
)
async def translate_endpoint(request: TranslateRequest) -> Any:
    result = translate_text(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
    )
    return TranslateResponse(
        translated_text=result["translated_text"],
        source_language=result["source_language"],
        target_language=result["target_language"],
    )


# ---------------------------------------------------------------------------
# POST /stories
# ---------------------------------------------------------------------------

@app.post(
    "/stories",
    status_code=status.HTTP_200_OK,
    summary="Generate contextual peer success stories using Bedrock",
)
async def stories_endpoint(request: StoriesRequest) -> Any:
    stories = generate_stories(
        state=request.state,
        district=request.district,
        scheme_ids=request.scheme_ids,
    )
    return {"status": "success", "stories": stories}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "service": "Nyaaya.ai Eligibility API",
        "version": "2.0.0",
        "status": "ok",
        "total_schemes": len(SCHEME_REGISTRY),
        "endpoints": [
            {"method": "POST", "path": "/interview", "description": "Multi-turn Hinglish interview (Bedrock)"},
            {"method": "POST", "path": "/evaluate", "description": "Direct profile eligibility evaluation"},
            {"method": "POST", "path": "/evaluate/family", "description": "Family mode evaluation"},
            {"method": "POST", "path": "/checklist", "description": "Deduplicated document checklist"},
            {"method": "POST", "path": "/report", "description": "PDF eligibility report"},
            {"method": "POST", "path": "/translate", "description": "Amazon Translate"},
            {"method": "POST", "path": "/stories", "description": "Peer success stories (Bedrock)"},
            {"method": "GET", "path": "/health", "description": "Health check"},
        ],
    }


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}


# ---------------------------------------------------------------------------
# AWS Lambda handler (Mangum)
# ---------------------------------------------------------------------------

handler = Mangum(app, lifespan="off")
