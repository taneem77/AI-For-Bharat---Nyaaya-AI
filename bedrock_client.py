"""
bedrock_client.py — Amazon Bedrock interview orchestration (Converse API)

Uses the unified Converse API which works with all Bedrock models
(Amazon Nova, Anthropic Claude, etc.) without model-specific request formats.

Handles: prompt construction, JSON extraction, malformed-response fallbacks.
All AWS errors are caught and return a safe Hinglish fallback.
"""
from __future__ import annotations

import json
import re
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import (
    AWS_REGION,
    BEDROCK_MODEL_ID,
    CONTEXT_WINDOW_TURNS,
    MAX_TOKENS_BEDROCK,
    logger,
)

# ---------------------------------------------------------------------------
# System prompt sent on every request
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an empathetic Indian Government Welfare Assistant named Nyaaya.
Your ONLY job: gather eligibility facts through natural Hinglish conversation.

STRICT RULES:
1. Be conversational — NOT a form. Ask exactly ONE question per turn.
2. Handle Hinglish naturally (code-mixing of Hindi + English is expected).
3. Extract ONLY these facts: age, income, marital_status, dependents, state,
   district, has_disability_cert, disability_percentage, life_event, is_rural, has_aadhaar.
4. NEVER determine eligibility yourself. Only extract facts.
5. After 6–8 turns (or when all key fields are collected), set interview_complete=true. Be efficient — ask about multiple related fields if natural (e.g. "Aapki age aur income kitni hai?").
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
    # 1. Try direct parse first
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
# Core interview function (Converse API)
# ---------------------------------------------------------------------------

def conduct_interview(
    user_input: str,
    conversation_history: list[dict[str, Any]],
    accumulated_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Call Bedrock via the unified Converse API with conversation context.

    ALWAYS returns a dict — never raises. On any AWS / parsing error, returns
    a safe Hinglish fallback so the endpoint stays at 200.
    """
    try:
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

        # Show the model what's already been collected
        collected = accumulated_data or {}
        all_fields = ["age", "income", "marital_status", "dependents", "state",
                      "district", "has_disability_cert", "disability_percentage",
                      "life_event", "is_rural", "has_aadhaar"]
        collected_str = json.dumps(collected, indent=2) if collected else "{}"
        missing = [f for f in all_fields if f not in collected]
        missing_str = ", ".join(missing) if missing else "NONE — all collected!"

        prompt = (
            f"Conversation History:\n{context_block}\n\n"
            f"ALREADY COLLECTED DATA (do NOT re-ask these):\n{collected_str}\n\n"
            f"STILL MISSING FIELDS: {missing_str}\n\n"
            f"User's Latest Input: \"{user_input}\"\n\n"
            "Ask about ONE of the missing fields. If all fields are collected, set interview_complete=true. "
            "Return ONLY valid JSON per the output format."
        )

        # Converse API — unified across all Bedrock models
        response = client.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[
                {"role": "user", "content": [{"text": prompt}]}
            ],
            inferenceConfig={
                "maxTokens": MAX_TOKENS_BEDROCK,
                "temperature": 0.3,
            },
        )

        assistant_text = response["output"]["message"]["content"][0]["text"]

        result = _extract_json(assistant_text)

        # Ensure required keys exist with safe defaults
        result.setdefault("next_question", "Kya aap thoda aur detail de sakte hain?")
        result.setdefault("extracted_data", {})
        result.setdefault("confidence", 0.5)
        result.setdefault("interview_complete", False)

        logger.info(
            "Bedrock response | complete=%s | confidence=%.2f | fields=%s",
            result["interview_complete"],
            result["confidence"],
            list(result["extracted_data"].keys()),
        )
        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error("Bedrock ClientError [%s]: %s", error_code, str(e))
        return _fallback_response(f"Bedrock error: {error_code}")

    except BotoCoreError as e:
        global _bedrock_client
        _bedrock_client = None
        logger.error(
            "Bedrock BotoCoreError [%s]: %s",
            type(e).__name__,
            str(e),
        )
        return _fallback_response(f"AWS configuration error: {type(e).__name__}")

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        logger.error("Bedrock response parse error: %s", str(e))
        return _fallback_response(str(e))

    except Exception as e:
        logger.exception("Unexpected error in conduct_interview: %s", str(e))
        return _fallback_response(f"Unexpected error: {type(e).__name__}")


# ---------------------------------------------------------------------------
# Fallback response (graceful degradation)
# ---------------------------------------------------------------------------

def _fallback_response(reason: str) -> dict[str, Any]:
    """Return a safe, conversation-continuing response on any error."""
    logger.warning("Using fallback response. Reason: %s", reason)
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


# ---------------------------------------------------------------------------
# Bedrock-powered contextual story generation (Converse API)
# ---------------------------------------------------------------------------

STORIES_PROMPT = """You are generating realistic, anonymised peer success stories for
Indian government welfare scheme applicants. These stories help users understand the
real-world application process.

Generate {count} stories for someone in {state}{district_clause} applying to these schemes: {schemes}.

Each story MUST be a JSON object with these fields:
- name: realistic Indian name (first name + last initial, e.g. "Savitri D.")
- district: a real district in {state}
- state: "{state}"
- age: age range string like "30-39", "40-49"
- scheme: the full scheme name
- status: "approved" (80% of stories) or "rejected" (20%)
- weeks: realistic processing time in weeks (integer)
- approval_rate: historical approval rate as integer 70-95
- blockers: list of 0-2 real-world blockers they faced (document issues, bureaucratic delays)
- tips: list of 2-3 practical, specific tips for the applicant

Make blockers and tips SPECIFIC to India's welfare bureaucracy (e.g. "BPL card expired",
"Gram Sevak unavailable on Tuesdays", "Private hospital cert rejected").

Return ONLY a JSON array of story objects. No markdown, no explanation.
"""


def generate_stories(
    state: str,
    district: str,
    scheme_ids: list[str],
) -> list[dict[str, Any]]:
    """
    Generate contextual peer stories via Bedrock Converse API.
    Falls back to hardcoded stories on any error.
    """
    if not scheme_ids:
        scheme_ids = ["general welfare schemes"]

    scheme_names = ", ".join(sid.replace("_", " ").title() for sid in scheme_ids)
    district_clause = f", {district} district" if district else ""
    count = min(len(scheme_ids) * 2, 6)

    prompt = STORIES_PROMPT.format(
        count=count,
        state=state,
        district_clause=district_clause,
        schemes=scheme_names,
    )

    try:
        client = _get_bedrock_client()

        response = client.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[{"text": "You are a helpful assistant that generates realistic Indian welfare scheme applicant stories. Return ONLY valid JSON arrays."}],
            messages=[
                {"role": "user", "content": [{"text": prompt}]}
            ],
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.5,
            },
        )

        text = response["output"]["message"]["content"][0]["text"]

        stories = _extract_json(text)
        # Handle both array and object-wrapped array
        if isinstance(stories, dict) and "stories" in stories:
            stories = stories["stories"]
        if isinstance(stories, list):
            logger.info("Generated %d stories for %s", len(stories), state)
            return stories
        return []

    except Exception as e:
        logger.error("Story generation failed: %s", str(e))
        return _fallback_stories(state, scheme_names)


def _fallback_stories(state: str, schemes: str) -> list[dict[str, Any]]:
    """Return hardcoded fallback stories when Bedrock is unavailable."""
    return [
        {
            "name": "Savitri D.",
            "district": "Pune",
            "state": state,
            "age": "40-49",
            "scheme": schemes.split(",")[0].strip() if schemes else "Welfare Scheme",
            "status": "approved",
            "weeks": 8,
            "approval_rate": 88,
            "blockers": ["Death certificate had spelling mismatch with Aadhaar name"],
            "tips": [
                "Get name corrected on documents BEFORE applying",
                "Carry 3 photocopies of every document",
                "Apply through Gram Sevak for faster processing",
            ],
        },
    ]
