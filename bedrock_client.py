"""
bedrock_client.py — Amazon Bedrock (Claude 3.5 Sonnet) interview orchestration

Handles: prompt construction, JSON extraction, malformed-response fallbacks.
Multi-level fallback strategy:
  1. Real Bedrock (if USE_REAL_BEDROCK=true and not DEMO_MODE)
  2. Enhanced smart mock (if USE_MOCK_FALLBACK=true or DEMO_MODE=true)
  3. Safe error response (should never be reached)
All AWS errors (including NoCredentialsError) are caught and return a safe
Hinglish fallback — the endpoint never throws a 500 due to Bedrock issues.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

import config
from config import (
    AWS_REGION,
    BEDROCK_MODEL_ID,
    CONTEXT_WINDOW_TURNS,
    MAX_TOKENS_BEDROCK,
    logger,
)

# ---------------------------------------------------------------------------
# System prompt sent to Claude on every request
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an empathetic Indian Government Welfare Assistant named Nyaaya.
Your ONLY job: gather eligibility facts through natural Hinglish conversation.

STRICT RULES:
1. Be conversational — NOT a form. Ask exactly ONE question per turn.
2. Handle Hinglish naturally (code-mixing of Hindi + English is expected).
3. Extract ONLY these facts: age, income, marital_status, dependents, state,
   district, has_disability_cert, disability_percentage, life_event, is_rural, has_aadhaar.
4. NEVER determine eligibility yourself. Only extract facts.
5. After 12–15 turns (or when all key fields are collected), set interview_complete=true.
6. If the user is confused, explain gently in simple Hindi + English.

VALID VALUES:
- marital_status: single | married | widow | divorced | separated
- life_event: widow | disabled | unemployed | elderly | farmer | student | none
- state: Maharashtra | Rajasthan | Uttar Pradesh (only these three)
- is_rural: true (village/gavaan) | false (shahar/city)

OUTPUT FORMAT — return ONLY valid JSON (no markdown, no explanation):
{
  "next_question": "<your next conversational question in Hinglish>",
  "extracted_data": {
    "<field>": <value>
  },
  "confidence": <0.0–1.0>,
  "interview_complete": false
}

EXAMPLES:
User: "Mera husband 5 saal pehle pass ho gaya"
Response: {"next_question": "Bahut dukh ki baat hai. Aapki umar kya hai?", "extracted_data": {"marital_status": "widow", "life_event": "widow"}, "confidence": 0.6, "interview_complete": false}

User: "Meri age 52 hai"
Response: {"next_question": "Aapke paas kitne bacche ya dependent hain?", "extracted_data": {"age": 52}, "confidence": 0.95, "interview_complete": false}
"""

# ---------------------------------------------------------------------------
# Bedrock client (lazy singleton — created on first use, reset on error)
# ---------------------------------------------------------------------------

_bedrock_client = None


def _get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
        )
    return _bedrock_client


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict[str, Any]:
    """
    Extract the first valid JSON object from text.
    Handles markdown-wrapped JSON (```json ... ```) and plain JSON.
    """
    # 1. Try direct parse first (Claude usually returns clean JSON)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences
    stripped = re.sub(r"```(?:json)?\s*", "", text).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 3. Find first {...} blob (greedy, handles extra prose)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from Bedrock response: {text[:300]}")


# ---------------------------------------------------------------------------
# Enhanced Smart Mock — simulates Claude without any AWS dependency
# ---------------------------------------------------------------------------

def _extract_amount(text: str) -> int | None:
    """Extract a monetary amount from text (handles ₹, Rs, rupees, k)."""
    # Remove commas and normalise
    text = text.replace(",", "")
    # Pattern: ₹12000, Rs 12000, 12000 rupees, 12k
    patterns = [
        r"(?:₹|rs\.?\s*)(\d+(?:\.\d+)?)(?:k\b)?",
        r"(\d+(?:\.\d+)?)(?:k)\s*(?:rupees|rs|₹|per month|monthly|income)?",
        r"(\d+(?:\.\d+)?)\s*(?:rupees|per month|monthly)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            # If "k" suffix present, multiply by 1000
            if "k" in text[m.start():m.end()].lower():
                val *= 1000
            return int(val)
    # Last resort: first standalone number ≥ 1000 (likely an amount)
    nums = re.findall(r'\b(\d{4,})\b', text)
    if nums:
        return int(nums[0])
    return None


# Ordered question flow for the smart mock
_QUESTION_FLOW = [
    # (missing_field, question_to_ask)
    ("marital_status", "Aapka marital status kya hai? Jaise — married, widow, single, ya divorced?"),
    ("age",            "Aapki umar kya hai? (Age in years)"),
    ("dependents",     "Aapke paas kitne bacche ya dependent family members hain?"),
    ("income",         "Aapki monthly income kitni hai? (Monthly income in rupees)"),
    ("state",          "Aap kis state mein rehte hain? Maharashtra, Rajasthan, ya Uttar Pradesh?"),
    ("district",       "Aapka district kya hai?"),
    ("is_rural",       "Aap village/gaav mein rehte hain ya shahar (city) mein?"),
    ("has_aadhaar",    "Kya aapke paas Aadhaar card hai?"),
]

_COMPLETE_QUESTION = (
    "Bahut shukriya! Maine aapki saari zaruri jaankari le li hai. "
    "Ab aap /evaluate endpoint se apni eligibility dekh sakte hain. "
    "Kya aapke koi aur sawaal hain?"
)


def _enhanced_mock_bedrock_response(
    user_input: str,
    conversation_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Smart mock that simulates Claude 3.5 Sonnet interview behavior.

    Logic:
      1. Parse conversation history to rebuild accumulated profile.
      2. Extract new data from current user_input using keyword matching.
      3. Merge and decide which field is still missing.
      4. Ask the next relevant question.
      5. After all key fields collected (or 14+ turns), mark interview_complete=true.
    """
    # ---- Step 1: Rebuild accumulated profile from history ----
    accumulated: dict[str, Any] = {}
    for turn in conversation_history:
        esf = turn.get("extracted_so_far", {})
        accumulated.update({k: v for k, v in esf.items() if v is not None})

    # ---- Step 2: Extract new data from user_input ----
    text = user_input.lower()
    extracted: dict[str, Any] = {}

    # Marital status — check widow FIRST (most specific) before generic married
    _widow_keywords = ["widow", "vidhwa", "pati nahi rahe", "nahi rahe pati", "guzar gaye", "pass ho gaya", "mar gaye"]
    _widow_phrase = re.search(
        r"husband[\w\s,]{0,30}(pass|guzar|mar|nahi rahe|died|death)", text
    )
    if any(w in text for w in _widow_keywords) or _widow_phrase:
        extracted["marital_status"] = "widow"
        extracted["life_event"] = "widow"
    elif any(w in text for w in ["married", "shadi", "vivah", "husband", "wife", "pati", "patni"]):
        if "marital_status" not in accumulated:
            extracted["marital_status"] = "married"
    elif any(w in text for w in ["single", "akela", "akeli", "unmarried", "koi nahi"]):
        if "marital_status" not in accumulated:
            extracted["marital_status"] = "single"
    elif any(w in text for w in ["divorced", "talak", "alag"]):
        if "marital_status" not in accumulated:
            extracted["marital_status"] = "divorced"

    # Age — look for number near age keyword
    # BUT skip "N saal pehle" / "N years ago" patterns (those are not the person's age)
    _is_years_ago = bool(re.search(r'\d+\s*(?:saal|varsh|sal|years?)\s+(?:pehle|ago|purane)', text))
    if not _is_years_ago and any(w in text for w in ["age", "saal", "umar", "varsh", "years old", "sal", "year"]):
        nums = re.findall(r'\b(\d{1,3})\b', user_input)
        if nums:
            age_val = int(nums[0])
            if 18 <= age_val <= 120:  # Realistic adult age range
                extracted["age"] = age_val
    elif "marital_status" in accumulated and not _is_years_ago and len(re.findall(r'\b(\d{1,3})\b', user_input)) == 1:
        # Only number in response, context says age was asked
        nums = re.findall(r'\b(\d{1,3})\b', user_input)
        if nums:
            age_val = int(nums[0])
            if 18 <= age_val <= 120 and "age" not in accumulated:
                extracted["age"] = age_val

    # Dependents / children
    if any(w in text for w in ["bacche", "children", "child", "bache", "beta", "beti", "dependent"]):
        nums = re.findall(r'\b(\d+)\b', user_input)
        if nums:
            extracted["dependents"] = int(nums[0])
        elif any(w in text for w in ["nahi", "no ", "zero", "koi nahi", "ek nahi"]):
            extracted["dependents"] = 0

    # Income
    if any(w in text for w in ["income", "paise", "rupees", "rupaye", "salary", "kamaai", "per month", "monthly", "₹"]):
        amount = _extract_amount(user_input)
        if amount is not None:
            extracted["income"] = amount
    elif "income" not in accumulated:
        # Might just be a number after income question
        amount = _extract_amount(user_input)
        if amount and amount >= 500:  # Reasonable income floor
            extracted["income"] = amount

    # State
    state_map = {
        "maharashtra": "Maharashtra",
        "mumbai": "Maharashtra",
        "pune": "Maharashtra",
        "nagpur": "Maharashtra",
        "rajasthan": "Rajasthan",
        "jaipur": "Rajasthan",
        "jodhpur": "Rajasthan",
        "udaipur": "Rajasthan",
        "uttar pradesh": "Uttar Pradesh",
        "up ": "Uttar Pradesh",
        "lucknow": "Uttar Pradesh",
        "varanasi": "Uttar Pradesh",
        "kanpur": "Uttar Pradesh",
        "agra": "Uttar Pradesh",
    }
    for kw, state_name in state_map.items():
        if kw in text:
            extracted["state"] = state_name
            break

    # District — capture if a state is known and something looks like a city/district name
    district_hints = {
        "pune": "Pune", "mumbai": "Mumbai", "nagpur": "Nagpur", "nashik": "Nashik",
        "thane": "Thane", "aurangabad": "Aurangabad",
        "jaipur": "Jaipur", "jodhpur": "Jodhpur", "udaipur": "Udaipur",
        "ajmer": "Ajmer", "kota": "Kota", "bikaner": "Bikaner",
        "lucknow": "Lucknow", "varanasi": "Varanasi", "kanpur": "Kanpur",
        "agra": "Agra", "allahabad": "Allahabad", "meerut": "Meerut",
    }
    for kw, dist_name in district_hints.items():
        if kw in text:
            extracted["district"] = dist_name
            break

    # Rural/Urban
    if any(w in text for w in ["village", "gaav", "gram", "rural", "pind"]):
        extracted["is_rural"] = True
    elif any(w in text for w in ["city", "shahar", "urban", "town", "nagar"]):
        extracted["is_rural"] = False

    # Aadhaar
    if any(w in text for w in ["aadhaar", "aadhar", "adhar"]):
        extracted["has_aadhaar"] = "nahi" not in text and "no" not in text

    # Disability
    if any(w in text for w in ["disability", "divyang", "viklang", "disabled"]):
        extracted["life_event"] = "disabled"
        extracted["has_disability_cert"] = True

    # ---- Step 3: Merge new extractions into accumulated ----
    accumulated.update({k: v for k, v in extracted.items() if v is not None})

    # ---- Step 4: Decide next question ----
    turn_count = len(conversation_history) + 1
    interview_complete = False
    next_question = _COMPLETE_QUESTION

    # Find first missing required field
    for field, question in _QUESTION_FLOW:
        if field not in accumulated:
            next_question = question
            break
    else:
        # All fields collected or turn cap reached
        interview_complete = True

    # Hard cap at 14 turns — complete the interview
    if turn_count >= 14:
        interview_complete = True
        next_question = _COMPLETE_QUESTION

    # ---- Step 5: Confidence based on data collected ----
    key_fields = {"marital_status", "age", "dependents", "income", "state", "district"}
    collected = key_fields.intersection(accumulated.keys())
    confidence = round(0.5 + 0.08 * len(collected), 2)
    confidence = min(confidence, 0.98)

    logger.info(
        "📝 Enhanced mock | turn=%d | extracted=%s | complete=%s",
        turn_count,
        list(extracted.keys()),
        interview_complete,
    )

    return {
        "next_question": next_question,
        "extracted_data": extracted,
        "confidence": confidence,
        "interview_complete": interview_complete,
    }


# ---------------------------------------------------------------------------
# Core interview function — multi-level fallback
# ---------------------------------------------------------------------------

def conduct_interview(
    user_input: str,
    conversation_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Multi-level fallback strategy:
      1. If DEMO_MODE or not USE_REAL_BEDROCK → go straight to enhanced mock.
      2. If USE_REAL_BEDROCK=true → try real Bedrock first.
         On any AWS error → fall back to enhanced mock (if USE_MOCK_FALLBACK=true).
      3. If mock also disabled → return a helpful error (should never happen).

    ALWAYS returns a dict — never raises. The endpoint stays at 200 OK.

    Args:
        user_input: Latest message from the user (Hinglish).
        conversation_history: List of ConversationTurn dicts (last N used).

    Returns:
        Dict with keys: next_question, extracted_data, confidence, interview_complete
    """

    # ── Path A: Demo mode or real Bedrock disabled ──────────────────────────
    if config.DEMO_MODE or not config.USE_REAL_BEDROCK:
        if config.DEMO_MODE:
            logger.info("🎬 DEMO MODE: Using enhanced mock fallback")
        else:
            logger.info("📝 USE_REAL_BEDROCK=false: Using enhanced mock fallback")
        return _enhanced_mock_bedrock_response(user_input, conversation_history)

    # ── Path B: Try real Bedrock ─────────────────────────────────────────────
    try:
        # Placed inside try so NoCredentialsError / EndpointResolutionError
        # is caught by the BotoCoreError handler below.
        client = _get_bedrock_client()

        # Build context window from last N turns
        recent = conversation_history[-CONTEXT_WINDOW_TURNS:]
        context_lines: list[str] = []
        for turn in recent:
            t = turn if isinstance(turn, dict) else turn.model_dump()
            context_lines.append(
                f"Turn {t['turn']}: User: {t['user_input']}\nAssistant: {t['assistant_response']}"
            )
        context_block = "\n".join(context_lines) if context_lines else "(This is the first turn)"

        prompt = (
            f"Conversation History:\n{context_block}\n\n"
            f"User's Latest Input: \"{user_input}\"\n\n"
            "Continue the interview. Ask the next relevant question. "
            "Return ONLY valid JSON per the output format."
        )

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-06-01",
                "max_tokens": MAX_TOKENS_BEDROCK,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            }
        )

        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        raw_body = response["body"].read().decode("utf-8")
        response_json = json.loads(raw_body)
        assistant_text: str = response_json["content"][0]["text"]

        result = _extract_json(assistant_text)

        # Ensure required keys exist with safe defaults
        result.setdefault("next_question", "Kya aap thoda aur detail de sakte hain?")
        result.setdefault("extracted_data", {})
        result.setdefault("confidence", 0.5)
        result.setdefault("interview_complete", False)

        logger.info(
            "✅ Real Bedrock: success | complete=%s | confidence=%.2f | fields=%s",
            result["interview_complete"],
            result["confidence"],
            list(result["extracted_data"].keys()),
        )
        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error("Bedrock ClientError [%s]: %s", error_code, str(e))
        return _handle_aws_failure(
            user_input, conversation_history, f"Bedrock ClientError: {error_code}"
        )

    except BotoCoreError as e:
        # Covers NoCredentialsError, EndpointResolutionError, and all boto
        # low-level errors that occur before a real HTTP response arrives.
        global _bedrock_client
        _bedrock_client = None          # force re-init on next warm request
        logger.warning(
            "⚠️  Bedrock %s: %s. Falling back to mock.",
            type(e).__name__,
            str(e),
        )
        return _handle_aws_failure(
            user_input, conversation_history, f"AWS config error: {type(e).__name__}"
        )

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        logger.error("Bedrock response parse error: %s", str(e))
        return _handle_aws_failure(
            user_input, conversation_history, f"Parse error: {e}"
        )

    except Exception as e:
        # Last-resort catch — guarantees no 500.
        logger.exception("Unexpected error in conduct_interview: %s", str(e))
        return _handle_aws_failure(
            user_input, conversation_history, f"Unexpected: {type(e).__name__}"
        )


def _handle_aws_failure(
    user_input: str,
    conversation_history: list[dict[str, Any]],
    reason: str,
) -> dict[str, Any]:
    """
    Called when real Bedrock fails.
    Falls back to enhanced mock if USE_MOCK_FALLBACK=true.
    Returns a safe error dict only if mock is also disabled.
    """
    if config.USE_MOCK_FALLBACK:
        logger.warning("⚠️  %s — falling back to enhanced mock.", reason)
        result = _enhanced_mock_bedrock_response(user_input, conversation_history)
        result["_fallback_reason"] = reason   # transparent metadata (not shown to user)
        return result

    # Both real AWS and fallback disabled — return a graceful error
    logger.error("❌ Both real Bedrock and mock fallback disabled! Reason: %s", reason)
    return _fallback_response(reason)


# ---------------------------------------------------------------------------
# Fallback response (graceful degradation — last resort)
# ---------------------------------------------------------------------------

def _fallback_response(reason: str) -> dict[str, Any]:
    """Return a safe, conversation-continuing response on any error."""
    logger.warning("Using last-resort fallback response. Reason: %s", reason)
    return {
        "next_question": (
            "Maafi kijiye, kuch technical samasya aayi. "
            "Kya aap apni baat dobara keh sakte hain?"
        ),
        "extracted_data": {},
        "confidence": 0.0,
        "interview_complete": False,
        "error": reason,
    }
