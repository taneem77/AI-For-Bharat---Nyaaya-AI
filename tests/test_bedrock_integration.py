"""
tests/test_bedrock_integration.py

Tests for bedrock_client.py — uses mocked boto3 to avoid real AWS calls.
Verifies: JSON extraction, fallbacks, context windowing, malformed responses.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from bedrock_client import _extract_json, _fallback_response, conduct_interview


# ---------------------------------------------------------------------------
# _extract_json helper tests
# ---------------------------------------------------------------------------

class TestExtractJson:
    def test_clean_json(self):
        data = {"next_question": "Hello?", "extracted_data": {"age": 30}}
        assert _extract_json(json.dumps(data)) == data

    def test_markdown_fenced_json(self):
        text = '```json\n{"next_question": "Hi?", "extracted_data": {}}\n```'
        out = _extract_json(text)
        assert out["next_question"] == "Hi?"

    def test_markdown_fence_no_lang(self):
        text = '```\n{"x": 1}\n```'
        out = _extract_json(text)
        assert out["x"] == 1

    def test_json_embedded_in_prose(self):
        text = 'Here is the answer: {"key": "value"} end of response'
        out = _extract_json(text)
        assert out["key"] == "value"

    def test_raises_on_no_json(self):
        with pytest.raises(ValueError, match="Could not extract"):
            _extract_json("This is plain text with no JSON.")

    def test_whitespace_handling(self):
        text = '   \n   {"a": 1}   \n   '
        assert _extract_json(text) == {"a": 1}


# ---------------------------------------------------------------------------
# _fallback_response tests
# ---------------------------------------------------------------------------

class TestFallbackResponse:
    def test_structure(self):
        out = _fallback_response("test error")
        assert out["next_question"]
        assert out["extracted_data"] == {}
        assert out["confidence"] == 0.0
        assert out["interview_complete"] is False
        assert "test error" in out["error"]


# ---------------------------------------------------------------------------
# conduct_interview — mocked Bedrock
# ---------------------------------------------------------------------------

def _make_bedrock_response(payload: dict) -> MagicMock:
    """Build a mock response matching Bedrock API shape."""
    body_bytes = json.dumps({"content": [{"text": json.dumps(payload)}]}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes

    mock_response = MagicMock()
    mock_response.__getitem__ = lambda self, key: mock_body if key == "body" else None
    return mock_response


@pytest.fixture()
def mock_bedrock_client():
    with patch("bedrock_client._get_bedrock_client") as mock_factory:
        client = MagicMock()
        mock_factory.return_value = client
        yield client


class TestConductInterview:
    def test_successful_extraction(self, mock_bedrock_client):
        payload = {
            "next_question": "Aapki umar kya hai?",
            "extracted_data": {"marital_status": "widow", "life_event": "widow"},
            "confidence": 0.7,
            "interview_complete": False,
        }
        mock_bedrock_client.invoke_model.return_value = _make_bedrock_response(payload)

        result = conduct_interview(
            "Mera husband 5 saal pehle pass ho gaya",
            [],
        )
        assert result["extracted_data"]["marital_status"] == "widow"
        assert result["interview_complete"] is False
        assert result["confidence"] == 0.7

    def test_missing_fields_use_defaults(self, mock_bedrock_client):
        """Claude returns partial JSON — missing keys get safe defaults."""
        payload = {"extracted_data": {"age": 52}}
        mock_bedrock_client.invoke_model.return_value = _make_bedrock_response(payload)

        result = conduct_interview("Meri age 52 hai", [])
        assert "next_question" in result
        assert result["interview_complete"] is False

    def test_markdown_wrapped_json(self, mock_bedrock_client):
        """Claude wraps JSON in markdown fences — must still parse."""
        inner = json.dumps({
            "next_question": "Acha, aage bataiye.",
            "extracted_data": {"age": 45},
            "confidence": 0.9,
            "interview_complete": False,
        })
        body_bytes = json.dumps({
            "content": [{"text": f"```json\n{inner}\n```"}]
        }).encode()
        mock_body = MagicMock()
        mock_body.read.return_value = body_bytes
        mock_resp = MagicMock()
        mock_resp.__getitem__ = lambda self, k: mock_body if k == "body" else None
        mock_bedrock_client.invoke_model.return_value = mock_resp

        result = conduct_interview("Meri age 45 hai", [])
        assert result["extracted_data"]["age"] == 45

    def test_context_window_passes_last_5_turns(self, mock_bedrock_client):
        """Verify only last CONTEXT_WINDOW_TURNS turns are sent (side effect check)."""
        from config import CONTEXT_WINDOW_TURNS

        payload = {
            "next_question": "Q?",
            "extracted_data": {},
            "confidence": 0.5,
            "interview_complete": False,
        }
        mock_bedrock_client.invoke_model.return_value = _make_bedrock_response(payload)

        history = [
            {"turn": i, "user_input": f"u{i}", "assistant_response": f"a{i}"}
            for i in range(1, 10)
        ]
        conduct_interview("latest", history)

        call_kwargs = mock_bedrock_client.invoke_model.call_args
        body_str = call_kwargs[1]["body"] if call_kwargs[1] else call_kwargs[0][0]
        body = json.loads(body_str)
        prompt_content = body["messages"][0]["content"]
        # Only last CONTEXT_WINDOW_TURNS turns should appear
        # Count "Turn X:" occurrences
        import re
        turns_mentioned = re.findall(r"Turn \d+:", prompt_content)
        assert len(turns_mentioned) <= CONTEXT_WINDOW_TURNS

    def test_bedrock_client_error_returns_fallback(self, mock_bedrock_client):
        from botocore.exceptions import ClientError
        mock_bedrock_client.invoke_model.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "rate limit"}},
            "InvokeModel",
        )
        result = conduct_interview("Any input", [])
        assert result["interview_complete"] is False
        assert "error" in result

    def test_unparseable_response_returns_fallback(self, mock_bedrock_client):
        body_bytes = json.dumps({
            "content": [{"text": "Sorry, I cannot help with that."}]
        }).encode()
        mock_body = MagicMock()
        mock_body.read.return_value = body_bytes
        mock_resp = MagicMock()
        mock_resp.__getitem__ = lambda self, k: mock_body if k == "body" else None
        mock_bedrock_client.invoke_model.return_value = mock_resp

        result = conduct_interview("Kuch bhi", [])
        assert result["interview_complete"] is False
        assert "error" in result

    def test_interview_complete_flag_propagated(self, mock_bedrock_client):
        payload = {
            "next_question": "Shukriya! Aapka interview complete hua.",
            "extracted_data": {},
            "confidence": 0.95,
            "interview_complete": True,
        }
        mock_bedrock_client.invoke_model.return_value = _make_bedrock_response(payload)
        result = conduct_interview("Done", [])
        assert result["interview_complete"] is True


# ---------------------------------------------------------------------------
# Test fixture: Sample Bedrock extraction scenarios (spec fixtures)
# ---------------------------------------------------------------------------

BEDROCK_FIXTURE_1 = {
    "description": "Widow with 3 children",
    "user_input": "Mera husband 2024 mein pass ho gaya, mere paas 3 bacche hain",
    "expected_extracted": {
        "marital_status": "widow",
        "dependents": 3,
        "life_event": "widow",
    },
    "expected_incomplete_fields": ["age"],
}

BEDROCK_FIXTURE_2 = {
    "description": "Direct age statement",
    "user_input": "Meri age 52 hai",
    "expected_extracted": {"age": 52},
}

BEDROCK_FIXTURE_3 = {
    "description": "Rural Rajasthan farmer",
    "user_input": "Main Rajasthan ke gaon se hoon, khet karta hoon",
    "expected_extracted": {
        "state": "Rajasthan",
        "is_rural": True,
        "life_event": "farmer",
    },
}

ALL_BEDROCK_FIXTURES = [BEDROCK_FIXTURE_1, BEDROCK_FIXTURE_2, BEDROCK_FIXTURE_3]


@pytest.mark.parametrize("fixture", ALL_BEDROCK_FIXTURES, ids=lambda f: f["description"])
def test_bedrock_fixture_expected_keys(fixture, mock_bedrock_client):
    """
    Simulate Bedrock returning matching extracted_data for each fixture.
    Validates that the extracted keys match expectations.
    """
    payload = {
        "next_question": "Next Q?",
        "extracted_data": fixture["expected_extracted"],
        "confidence": 0.8,
        "interview_complete": False,
    }
    mock_bedrock_client.invoke_model.return_value = _make_bedrock_response(payload)

    result = conduct_interview(fixture["user_input"], [])
    for key, expected_val in fixture["expected_extracted"].items():
        assert result["extracted_data"][key] == expected_val, (
            f"[{fixture['description']}] Field '{key}' mismatch"
        )
