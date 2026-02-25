"""
bedrock_client.py — Amazon Bedrock (Claude 3.5 Sonnet) interview orchestration

Handles: prompt construction, JSON extraction, malformed-response fallbacks.
All AWS errors (including NoCredentialsError) are caught and return a safe
Hinglish fallback — the endpoint never throws a 500 due to Bedrock issues.
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
# Core interview function
# ---------------------------------------------------------------------------

def conduct_interview(
    user_input: str,
    conversation_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Call Claude 3.5 Sonnet via Bedrock with the conversation context.

    ALWAYS returns a dict — never raises. On any AWS / parsing error, returns
    a safe Hinglish fallback so the endpoint stays at 200.

    Args:
        user_input: Latest message from the user (Hinglish).
        conversation_history: List of ConversationTurn dicts (last N used).

    Returns:
        Dict with keys: next_question, extracted_data, confidence, interview_complete
    """
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
        # Covers NoCredentialsError, EndpointResolutionError, and all boto
        # low-level errors that occur before a real HTTP response arrives.
        global _bedrock_client
        _bedrock_client = None          # force re-init on next warm request
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
        # Last-resort catch — should never be reached, but guarantees no 500.
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
