"""
tests/test_api_endpoints.py

FastAPI TestClient integration tests for /interview and /evaluate.
Mocks Bedrock (no real AWS) and uses MockDynamoDBClient.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main as app_module
from dynamodb_utils import MockDynamoDBClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_db(monkeypatch):
    """Inject a fresh MockDynamoDBClient for every test."""
    mock_db = MockDynamoDBClient()
    monkeypatch.setattr(app_module, "_db", mock_db)
    return mock_db


@pytest.fixture()
def client():
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def _mock_bedrock_result(payload: dict):
    """Patch conduct_interview in main to return payload."""
    return patch("main.conduct_interview", return_value=payload)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# POST /interview
# ---------------------------------------------------------------------------

class TestInterviewEndpoint:
    _BASE_PAYLOAD = {
        "next_question": "Aapki umar kya hai?",
        "extracted_data": {"marital_status": "widow", "life_event": "widow"},
        "confidence": 0.7,
        "interview_complete": False,
    }

    def test_new_session_success(self, client):
        with _mock_bedrock_result(self._BASE_PAYLOAD):
            r = client.post("/interview", json={
                "user_input": "Mera husband pass ho gaya",
                "session_id": "test_sess_001",
            })
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "success"
        assert body["turn"] == 1
        assert body["interview_complete"] is False
        assert "next_question" in body
        assert body["extracted_so_far"]["marital_status"] == "widow"

    def test_session_persists_across_turns(self, client):
        payload_turn1 = {
            "next_question": "Aapki umar?",
            "extracted_data": {"marital_status": "widow"},
            "confidence": 0.6,
            "interview_complete": False,
        }
        payload_turn2 = {
            "next_question": "Aapka district?",
            "extracted_data": {"age": 52},
            "confidence": 0.95,
            "interview_complete": False,
        }
        with _mock_bedrock_result(payload_turn1):
            r1 = client.post("/interview", json={
                "user_input": "Mera husband gaye",
                "session_id": "persist_sess",
            })
        with _mock_bedrock_result(payload_turn2):
            r2 = client.post("/interview", json={
                "user_input": "52 saal",
                "session_id": "persist_sess",
            })
        assert r1.json()["turn"] == 1
        assert r2.json()["turn"] == 2
        # Turn 2 merged extraction should include widow + age
        assert r2.json()["extracted_so_far"]["marital_status"] == "widow"
        assert r2.json()["extracted_so_far"]["age"] == 52

    def test_already_complete_session_returns_early(self, client, reset_db):
        """If session is already complete, skip Bedrock and return early."""
        from models import InterviewState
        from dynamodb_utils import save_interview_state

        complete_state = InterviewState(
            user_id="done_sess",
            interview_complete=True,
            turn_count=12,
        )
        save_interview_state("done_sess", complete_state, reset_db)

        # Should NOT call Bedrock
        with patch("main.conduct_interview") as mock_ci:
            r = client.post("/interview", json={
                "user_input": "Any message",
                "session_id": "done_sess",
            })
            mock_ci.assert_not_called()

        assert r.status_code == 200
        assert r.json()["interview_complete"] is True

    def test_missing_user_input_returns_422(self, client):
        r = client.post("/interview", json={"session_id": "xyz"})
        assert r.status_code == 422

    def test_missing_session_id_returns_422(self, client):
        r = client.post("/interview", json={"user_input": "Hello"})
        assert r.status_code == 422

    def test_empty_user_input_returns_422(self, client):
        r = client.post("/interview", json={
            "user_input": "",
            "session_id": "xyz",
        })
        assert r.status_code == 422

    def test_bedrock_error_returns_fallback_not_500(self, client):
        """Even if Bedrock fails, interview should return 200 with fallback."""
        with patch("main.conduct_interview", return_value={
            "next_question": "Maafi kijiye, dobara keh sakte hain?",
            "extracted_data": {},
            "confidence": 0.0,
            "interview_complete": False,
            "error": "Bedrock error",
        }):
            r = client.post("/interview", json={
                "user_input": "Hello",
                "session_id": "err_sess",
            })
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# POST /evaluate
# ---------------------------------------------------------------------------

_WIDOW_PROFILE = {
    "age": 52,
    "income": 12_000,
    "marital_status": "widow",
    "dependents": 2,
    "state": "Maharashtra",
    "district": "Pune",
    "has_disability_cert": False,
    "disability_percentage": None,
    "life_event": "widow",
    "is_rural": True,
    "has_aadhaar": True,
}

_DISABLED_PROFILE = {
    "age": 35,
    "income": 8_000,
    "marital_status": "single",
    "dependents": 0,
    "state": "Maharashtra",
    "district": "Nagpur",
    "has_disability_cert": True,
    "disability_percentage": 60,
    "life_event": "disabled",
    "is_rural": True,
    "has_aadhaar": True,
}

_NREGA_PROFILE = {
    "age": 30,
    "income": 15_000,
    "marital_status": "married",
    "dependents": 3,
    "state": "Rajasthan",
    "district": "Jaipur",
    "has_disability_cert": False,
    "disability_percentage": None,
    "life_event": "none",
    "is_rural": True,
    "has_aadhaar": True,
}


class TestEvaluateEndpoint:
    def test_widow_eligible_for_widow_pension(self, client):
        r = client.post("/evaluate", json=_WIDOW_PROFILE)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "success"
        eligible_ids = {s["scheme_id"] for s in body["eligible_schemes"] if s["eligible"]}
        assert "widow_pension_mh" in eligible_ids

    def test_disabled_eligible_for_disability_allowance(self, client):
        r = client.post("/evaluate", json=_DISABLED_PROFILE)
        assert r.status_code == 200
        eligible_ids = {s["scheme_id"] for s in r.json()["eligible_schemes"] if s["eligible"]}
        assert "disability_allowance" in eligible_ids

    def test_rural_rajasthan_eligible_for_nrega(self, client):
        r = client.post("/evaluate", json=_NREGA_PROFILE)
        assert r.status_code == 200
        eligible_ids = {s["scheme_id"] for s in r.json()["eligible_schemes"] if s["eligible"]}
        assert "nrega" in eligible_ids

    def test_strategy_is_sorted_by_rank(self, client):
        r = client.post("/evaluate", json=_WIDOW_PROFILE)
        strategy = r.json()["strategy"]
        if len(strategy) > 1:
            ranks = [s["rank"] for s in strategy]
            assert ranks == sorted(ranks)

    def test_summary_contains_required_keys(self, client):
        r = client.post("/evaluate", json=_WIDOW_PROFILE)
        summary = r.json()["summary"]
        assert "total_monthly_benefit" in summary
        assert "first_year_total" in summary
        assert "documents_to_obtain" in summary
        assert "estimated_total_timeline_weeks" in summary

    def test_validation_error_age_out_of_range(self, client):
        bad = {**_WIDOW_PROFILE, "age": 200}
        r = client.post("/evaluate", json=bad)
        assert r.status_code == 422   # FastAPI auto-validates Pydantic

    def test_validation_error_bad_state(self, client):
        bad = {**_WIDOW_PROFILE, "state": "Bihar"}
        r = client.post("/evaluate", json=bad)
        assert r.status_code == 422

    def test_validation_error_disability_cert_no_percentage(self, client):
        bad = {**_DISABLED_PROFILE, "disability_percentage": None}
        r = client.post("/evaluate", json=bad)
        assert r.status_code == 422

    def test_validation_error_elderly_too_young(self, client):
        bad = {**_WIDOW_PROFILE, "life_event": "elderly", "age": 30}
        r = client.post("/evaluate", json=bad)
        assert r.status_code == 422

    def test_ineligible_person_returns_success_with_false_eligible(self, client):
        """High income person should get success response with eligible=False on all."""
        rich = {**_WIDOW_PROFILE, "income": 999_999}
        r = client.post("/evaluate", json=rich)
        assert r.status_code == 200
        body = r.json()
        assert all(not s["eligible"] for s in body["eligible_schemes"])

    def test_state_case_insensitive(self, client):
        """State field should normalise case."""
        profile = {**_NREGA_PROFILE, "state": "rajasthan"}
        r = client.post("/evaluate", json=profile)
        assert r.status_code == 200

    def test_state_alias_up(self, client):
        profile = {**_NREGA_PROFILE, "state": "UP"}
        r = client.post("/evaluate", json=profile)
        assert r.status_code == 200

    def test_mutual_exclusivity_applied(self, client):
        """
        Spec test: age=65, widow, low income → eligible for widow_pension.
        old_age_pension is not in our rules but test ME logic indirectly.
        Widow + NREGA should both appear (no conflict between them).
        """
        profile = {
            "age": 55,
            "income": 10_000,
            "marital_status": "widow",
            "dependents": 1,
            "state": "Maharashtra",
            "district": "Nashik",
            "has_disability_cert": False,
            "disability_percentage": None,
            "life_event": "widow",
            "is_rural": True,
            "has_aadhaar": True,
        }
        r = client.post("/evaluate", json=profile)
        assert r.status_code == 200
        eligible_ids = {s["scheme_id"] for s in r.json()["eligible_schemes"] if s["eligible"]}
        assert "widow_pension_mh" in eligible_ids
        assert "nrega" in eligible_ids

    def test_total_monthly_benefit_matches_eligible_schemes(self, client):
        r = client.post("/evaluate", json=_WIDOW_PROFILE)
        body = r.json()
        expected_monthly = sum(
            s["benefit_monthly"] for s in body["eligible_schemes"] if s["eligible"]
        )
        assert body["summary"]["total_monthly_benefit"] == expected_monthly
