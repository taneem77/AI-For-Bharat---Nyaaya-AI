"""
tests/test_fallback.py — Comprehensive tests for the fallback + demo mode system.

Tests cover:
  1. Enhanced mock Bedrock response logic (keyword extraction, question flow)
  2. Demo mode behavior (mock always used, log output)
  3. MockDynamoDBClient persistence, TTL, concurrent sessions
  4. Multi-level fallback: real Bedrock failure → mock
  5. Full interview flow end-to-end with mock (no AWS)
  6. Session persistence across multiple /interview calls
"""
from __future__ import annotations

import time
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is on path (conftest.py handles this normally)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# 1. Enhanced Mock Bedrock Response Tests
# ---------------------------------------------------------------------------

class TestEnhancedMockBedrockResponse(unittest.TestCase):
    """Tests for the smart mock that simulates Claude's interview behavior."""

    def setUp(self):
        # Import after path setup, inside each test class to pick up any monkeypatching
        from bedrock_client import _enhanced_mock_bedrock_response
        self.mock_fn = _enhanced_mock_bedrock_response

    def test_returns_required_keys(self):
        """Mock always returns the four required keys."""
        result = self.mock_fn("Hello", [])
        self.assertIn("next_question", result)
        self.assertIn("extracted_data", result)
        self.assertIn("confidence", result)
        self.assertIn("interview_complete", result)

    def test_extracts_widow_status(self):
        """Detects widow keywords in Hinglish."""
        result = self.mock_fn("Mera husband 5 saal pehle pass ho gaya", [])
        self.assertEqual(result["extracted_data"].get("marital_status"), "widow")
        self.assertEqual(result["extracted_data"].get("life_event"), "widow")

    def test_extracts_age(self):
        """Extracts age from 'Meri age 52 hai'."""
        result = self.mock_fn("Meri age 52 hai", [])
        self.assertEqual(result["extracted_data"].get("age"), 52)

    def test_extracts_dependents(self):
        """Extracts dependents count."""
        result = self.mock_fn("Mere 2 bacche hain", [])
        self.assertEqual(result["extracted_data"].get("dependents"), 2)

    def test_extracts_income_plain(self):
        """Extracts income amount — plain number."""
        result = self.mock_fn("Monthly income 12000 hai", [])
        self.assertEqual(result["extracted_data"].get("income"), 12000)

    def test_extracts_income_rupee_symbol(self):
        """Extracts income with ₹ symbol."""
        result = self.mock_fn("Meri income ₹15000 per month hai", [])
        self.assertEqual(result["extracted_data"].get("income"), 15000)

    def test_extracts_maharashtra(self):
        """Detects Maharashtra from state keywords."""
        result = self.mock_fn("Main pune mein rehti hoon", [])
        self.assertEqual(result["extracted_data"].get("state"), "Maharashtra")

    def test_extracts_rural_true(self):
        """Detects village/rural keyword."""
        result = self.mock_fn("Main village mein rehti hoon", [])
        self.assertTrue(result["extracted_data"].get("is_rural"))

    def test_extracts_urban_false(self):
        """Detects city/urban keyword."""
        result = self.mock_fn("Main Mumbai city mein rehti hoon", [])
        self.assertFalse(result["extracted_data"].get("is_rural"))

    def test_confidence_increases_with_data(self):
        """More data collected → higher confidence."""
        # Turn 1: blank slate
        r1 = self.mock_fn("Hello", [])
        # Turn 4: lots of data accumulated in history
        history = [
            {
                "turn": 1, "user_input": "widow", "assistant_response": "q1",
                "extracted_so_far": {"marital_status": "widow", "age": 50, "income": 10000, "dependents": 2},
            }
        ]
        r4 = self.mock_fn("Main Jaipur mein hoon", history)
        self.assertGreater(r4["confidence"], r1["confidence"])

    def test_interview_complete_after_cap(self):
        """interview_complete=True when turn ≥ 14."""
        # Build 14 prior turns
        history = [
            {
                "turn": i, "user_input": f"msg {i}", "assistant_response": "q",
                "extracted_so_far": {},
            }
            for i in range(1, 14)
        ]
        result = self.mock_fn("Some final input", history)
        self.assertTrue(result["interview_complete"])

    def test_question_flow_progresses(self):
        """After marital_status known, next question should be about age."""
        history = [
            {
                "turn": 1, "user_input": "widow", "assistant_response": "q1",
                "extracted_so_far": {"marital_status": "widow", "life_event": "widow"},
            }
        ]
        result = self.mock_fn("Meri age 45 hai", history)
        # After age is extracted, mock should ask about dependents next
        next_q = result["next_question"].lower()
        # Should NOT still be asking about marital status or age
        self.assertNotIn("marital status", next_q)


# ---------------------------------------------------------------------------
# 2. MockDynamoDBClient Tests
# ---------------------------------------------------------------------------

class TestMockDynamoDBClient(unittest.TestCase):
    """Tests for the in-memory DynamoDB mock."""

    def setUp(self):
        from dynamodb_utils import MockDynamoDBClient
        self.db = MockDynamoDBClient()

    def test_put_and_get_item(self):
        """Basic put → get roundtrip."""
        item = {
            "session_id": "test_session_1",
            "turn_count": 1,
            "interview_complete": False,
            "conversation_history": "[]",
            "extracted_profile": None,
            "timestamp": int(time.time()),
            "ttl": int(time.time()) + 86400,
        }
        self.db.put_item(item)
        result = self.db.get_item("test_session_1")
        self.assertIsNotNone(result)
        self.assertEqual(result["session_id"], "test_session_1")

    def test_get_nonexistent_returns_none(self):
        """GET on unknown session_id returns None."""
        result = self.db.get_item("does_not_exist")
        self.assertIsNone(result)

    def test_ttl_expired_returns_none(self):
        """Items with past TTL are expired and return None."""
        item = {
            "session_id": "expired_session",
            "turn_count": 0,
            "interview_complete": False,
            "conversation_history": "[]",
            "extracted_profile": None,
            "timestamp": int(time.time()) - 100,
            "ttl": int(time.time()) - 1,   # already expired
        }
        self.db.put_item(item)
        result = self.db.get_item("expired_session")
        self.assertIsNone(result)

    def test_ttl_not_expired_returns_item(self):
        """Items with future TTL are returned correctly."""
        item = {
            "session_id": "live_session",
            "turn_count": 2,
            "interview_complete": False,
            "conversation_history": "[]",
            "extracted_profile": None,
            "timestamp": int(time.time()),
            "ttl": int(time.time()) + 86400,  # 24 hours future
        }
        self.db.put_item(item)
        result = self.db.get_item("live_session")
        self.assertIsNotNone(result)

    def test_concurrent_sessions_isolated(self):
        """Multiple sessions stored and retrieved correctly."""
        for i in range(5):
            self.db.put_item({
                "session_id": f"session_{i}",
                "turn_count": i,
                "interview_complete": False,
                "conversation_history": "[]",
                "extracted_profile": None,
                "timestamp": int(time.time()),
                "ttl": int(time.time()) + 86400,
            })

        for i in range(5):
            result = self.db.get_item(f"session_{i}")
            self.assertIsNotNone(result)
            self.assertEqual(result["turn_count"], i)

    def test_session_count_property(self):
        """session_count returns number of non-expired sessions."""
        self.db.clear()
        self.db.put_item({
            "session_id": "count_test_1",
            "turn_count": 1,
            "interview_complete": False,
            "conversation_history": "[]",
            "extracted_profile": None,
            "timestamp": int(time.time()),
            "ttl": int(time.time()) + 86400,
        })
        self.db.put_item({
            "session_id": "count_test_expired",
            "turn_count": 1,
            "interview_complete": False,
            "conversation_history": "[]",
            "extracted_profile": None,
            "timestamp": int(time.time()) - 200,
            "ttl": int(time.time()) - 1,  # expired
        })
        # Only the non-expired session should count
        self.assertEqual(self.db.session_count, 1)

    def test_update_existing_session(self):
        """Putting same session_id twice overwrites the previous value."""
        item = {
            "session_id": "update_test",
            "turn_count": 1,
            "interview_complete": False,
            "conversation_history": "[]",
            "extracted_profile": None,
            "timestamp": int(time.time()),
            "ttl": int(time.time()) + 86400,
        }
        self.db.put_item(item)

        item["turn_count"] = 3
        item["interview_complete"] = True
        self.db.put_item(item)

        result = self.db.get_item("update_test")
        self.assertIsNotNone(result)
        self.assertEqual(result["turn_count"], 3)
        self.assertTrue(result["interview_complete"])

    def test_clear_wipes_all_sessions(self):
        """clear() removes all stored sessions."""
        self.db.put_item({
            "session_id": "to_clear",
            "turn_count": 1,
            "interview_complete": False,
            "conversation_history": "[]",
            "extracted_profile": None,
            "timestamp": int(time.time()),
            "ttl": int(time.time()) + 86400,
        })
        self.db.clear()
        self.assertIsNone(self.db.get_item("to_clear"))
        self.assertEqual(self.db.session_count, 0)


# ---------------------------------------------------------------------------
# 3. Demo Mode Tests (via config flags)
# ---------------------------------------------------------------------------

class TestDemoMode(unittest.TestCase):
    """Tests that DEMO_MODE flag forces mock and never calls real AWS."""

    def test_demo_mode_forces_use_real_bedrock_false(self):
        """When DEMO_MODE=true, USE_REAL_BEDROCK must be False."""
        with patch.dict("os.environ", {"DEMO_MODE": "true"}):
            import importlib
            import config as cfg
            importlib.reload(cfg)
            self.assertFalse(cfg.USE_REAL_BEDROCK)

    def test_demo_mode_forces_use_real_dynamodb_false(self):
        """When DEMO_MODE=true, USE_REAL_DYNAMODB must be False."""
        with patch.dict("os.environ", {"DEMO_MODE": "true"}):
            import importlib
            import config as cfg
            importlib.reload(cfg)
            self.assertFalse(cfg.USE_REAL_DYNAMODB)

    def test_production_mode_respects_real_bedrock_flag(self):
        """When DEMO_MODE=false and USE_REAL_BEDROCK=true, flag stays True."""
        with patch.dict("os.environ", {"DEMO_MODE": "false", "USE_REAL_BEDROCK": "true"}):
            import importlib
            import config as cfg
            importlib.reload(cfg)
            self.assertTrue(cfg.USE_REAL_BEDROCK)

    def test_conduct_interview_uses_mock_in_demo_mode(self):
        """conduct_interview skips boto3 entirely when DEMO_MODE=true."""
        with patch("bedrock_client.config") as mock_config:
            mock_config.DEMO_MODE = True
            mock_config.USE_REAL_BEDROCK = False
            mock_config.USE_MOCK_FALLBACK = True

            from bedrock_client import conduct_interview
            with patch("bedrock_client._get_bedrock_client") as mock_client:
                result = conduct_interview("Test input", [])
                # boto3 client should NEVER be called in demo mode
                mock_client.assert_not_called()

            self.assertIn("next_question", result)
            self.assertIn("extracted_data", result)
            self.assertIsInstance(result["interview_complete"], bool)

    def test_conduct_interview_mock_when_real_bedrock_disabled(self):
        """conduct_interview returns mock when USE_REAL_BEDROCK=false."""
        with patch("bedrock_client.config") as mock_config:
            mock_config.DEMO_MODE = False
            mock_config.USE_REAL_BEDROCK = False
            mock_config.USE_MOCK_FALLBACK = True

            from bedrock_client import conduct_interview
            result = conduct_interview("Meri age 30 hai", [])

            self.assertIn("next_question", result)
            self.assertNotIn("error", result)


# ---------------------------------------------------------------------------
# 4. Multi-level Fallback Tests (AWS failure → mock)
# ---------------------------------------------------------------------------

class TestMultiLevelFallback(unittest.TestCase):
    """Tests that AWS failures automatically fall back to mock."""

    def test_client_error_falls_back_to_mock(self):
        """ClientError from boto3 → falls back to enhanced mock."""
        from botocore.exceptions import ClientError
        from bedrock_client import conduct_interview

        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Denied"}}
        fake_client = MagicMock()
        fake_client.invoke_model.side_effect = ClientError(error_response, "InvokeModel")

        with patch("bedrock_client.config") as mock_config, \
             patch("bedrock_client._get_bedrock_client", return_value=fake_client):
            mock_config.DEMO_MODE = False
            mock_config.USE_REAL_BEDROCK = True
            mock_config.USE_MOCK_FALLBACK = True

            result = conduct_interview("Mera husband pass ho gaya", [])

        # Should NOT raise; should return mock data
        self.assertIn("next_question", result)
        self.assertNotEqual(result["next_question"], "")
        self.assertIn("_fallback_reason", result)  # metadata added on fallback

    def test_no_credentials_falls_back_to_mock(self):
        """NoCredentialsError → falls back to enhanced mock."""
        from botocore.exceptions import NoCredentialsError
        from bedrock_client import conduct_interview

        fake_client = MagicMock()
        fake_client.invoke_model.side_effect = NoCredentialsError()

        with patch("bedrock_client.config") as mock_config, \
             patch("bedrock_client._get_bedrock_client", return_value=fake_client):
            mock_config.DEMO_MODE = False
            mock_config.USE_REAL_BEDROCK = True
            mock_config.USE_MOCK_FALLBACK = True

            result = conduct_interview("Meri age 35 hai", [])

        self.assertIn("next_question", result)
        self.assertIn("_fallback_reason", result)

    def test_fallback_disabled_returns_error_response(self):
        """When USE_MOCK_FALLBACK=false, fallback returns error dict (not raises)."""
        from botocore.exceptions import NoCredentialsError
        from bedrock_client import conduct_interview

        fake_client = MagicMock()
        fake_client.invoke_model.side_effect = NoCredentialsError()

        with patch("bedrock_client.config") as mock_config, \
             patch("bedrock_client._get_bedrock_client", return_value=fake_client):
            mock_config.DEMO_MODE = False
            mock_config.USE_REAL_BEDROCK = True
            mock_config.USE_MOCK_FALLBACK = False  # fallback disabled

            result = conduct_interview("Input text", [])

        # Should still return a dict with "error" key — never raises
        self.assertIn("next_question", result)
        self.assertIn("error", result)
        self.assertEqual(result["interview_complete"], False)


# ---------------------------------------------------------------------------
# 5. Session Persistence Across Multiple Calls (MockDB)
# ---------------------------------------------------------------------------

class TestSessionPersistenceMockDB(unittest.TestCase):
    """Verify sessions are correctly maintained across multiple save/load cycles."""

    def setUp(self):
        from dynamodb_utils import MockDynamoDBClient
        self.db = MockDynamoDBClient()

    def test_save_and_load_interview_state(self):
        """save_interview_state → load_interview_state roundtrip."""
        from dynamodb_utils import save_interview_state, load_interview_state
        from models import InterviewState

        state = InterviewState(user_id="persist_test")
        save_interview_state("persist_test", state, self.db)

        loaded = load_interview_state("persist_test", self.db)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.turn_count, 0)
        self.assertFalse(loaded.interview_complete)

    def test_save_multiple_turns_persists_all(self):
        """Multiple add_turn calls persist correctly."""
        from dynamodb_utils import save_interview_state, load_interview_state
        from models import InterviewState

        state = InterviewState(user_id="multi_turn_test")
        state.add_turn("Input 1", "Response 1", {"marital_status": "widow"})
        state.add_turn("Input 2", "Response 2", {"age": 45})
        save_interview_state("multi_turn_test", state, self.db)

        loaded = load_interview_state("multi_turn_test", self.db)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.turn_count, 2)
        self.assertEqual(len(loaded.conversation_history), 2)

    def test_update_session_overwrites_old(self):
        """Saving same session_id twice keeps only the latest state."""
        from dynamodb_utils import save_interview_state, load_interview_state
        from models import InterviewState

        state = InterviewState(user_id="overwrite_test")
        state.add_turn("Input 1", "Response 1", {})
        save_interview_state("overwrite_test", state, self.db)

        state.add_turn("Input 2", "Response 2", {})
        save_interview_state("overwrite_test", state, self.db)

        loaded = load_interview_state("overwrite_test", self.db)
        self.assertEqual(loaded.turn_count, 2)

    def test_different_sessions_dont_interfere(self):
        """Two separate sessions are completely isolated."""
        from dynamodb_utils import save_interview_state, load_interview_state
        from models import InterviewState

        state_a = InterviewState(user_id="session_a")
        state_a.add_turn("A input", "A response", {"age": 30})
        save_interview_state("session_a", state_a, self.db)

        state_b = InterviewState(user_id="session_b")
        state_b.add_turn("B input", "B response", {"age": 50})
        state_b.add_turn("B2 input", "B2 response", {"income": 20000})
        save_interview_state("session_b", state_b, self.db)

        loaded_a = load_interview_state("session_a", self.db)
        loaded_b = load_interview_state("session_b", self.db)

        self.assertEqual(loaded_a.turn_count, 1)
        self.assertEqual(loaded_b.turn_count, 2)

    def test_expired_session_returns_none_on_load(self):
        """Expired sessions are treated as not found."""
        from dynamodb_utils import load_interview_state
        import json

        expired_item = {
            "session_id": "expired_test",
            "turn_count": 3,
            "interview_complete": False,
            "conversation_history": "[]",
            "extracted_profile": None,
            "timestamp": int(time.time()) - 100,
            "ttl": int(time.time()) - 1,  # already expired
        }
        self.db.put_item(expired_item)

        loaded = load_interview_state("expired_test", self.db)
        self.assertIsNone(loaded)


# ---------------------------------------------------------------------------
# 6. Full Mock Interview Flow (end-to-end, no AWS)
# ---------------------------------------------------------------------------

class TestFullMockInterviewFlow(unittest.TestCase):
    """Simulate a realistic multi-turn interview using the smart mock."""

    def test_realistic_widow_interview_flow(self):
        """Simulate 4-turn conversation: widow → age → dependents → income."""
        from bedrock_client import _enhanced_mock_bedrock_response

        conversation_history = []

        # Turn 1: widow
        r1 = _enhanced_mock_bedrock_response(
            "Mera husband 5 saal pehle pass ho gaya", conversation_history
        )
        self.assertEqual(r1["extracted_data"]["marital_status"], "widow")
        self.assertFalse(r1["interview_complete"])
        # Next question should be about age (marital_status known, age unknown)
        self.assertIn("umar", r1["next_question"].lower())

        # Add turn 1 to history
        conversation_history.append({
            "turn": 1,
            "user_input": "Mera husband 5 saal pehle pass ho gaya",
            "assistant_response": r1["next_question"],
            "extracted_so_far": r1["extracted_data"],
        })

        # Turn 2: age
        r2 = _enhanced_mock_bedrock_response("Meri age 52 hai", conversation_history)
        self.assertEqual(r2["extracted_data"]["age"], 52)
        self.assertFalse(r2["interview_complete"])

        conversation_history.append({
            "turn": 2,
            "user_input": "Meri age 52 hai",
            "assistant_response": r2["next_question"],
            "extracted_so_far": {**conversation_history[-1]["extracted_so_far"], **r2["extracted_data"]},
        })

        # Turn 3: dependents
        r3 = _enhanced_mock_bedrock_response("Mere 2 bacche hain", conversation_history)
        self.assertEqual(r3["extracted_data"]["dependents"], 2)

        conversation_history.append({
            "turn": 3,
            "user_input": "Mere 2 bacche hain",
            "assistant_response": r3["next_question"],
            "extracted_so_far": {**conversation_history[-1]["extracted_so_far"], **r3["extracted_data"]},
        })

        # Turn 4: income
        r4 = _enhanced_mock_bedrock_response("Monthly income ₹12000 hai", conversation_history)
        self.assertEqual(r4["extracted_data"]["income"], 12000)

        # All responses are valid dicts — no exceptions thrown
        for r in [r1, r2, r3, r4]:
            self.assertIsInstance(r["next_question"], str)
            self.assertIsInstance(r["extracted_data"], dict)
            self.assertIsInstance(r["confidence"], float)
            self.assertIsInstance(r["interview_complete"], bool)

    def test_mock_never_raises(self):
        """Smart mock should handle any input without raising."""
        from bedrock_client import _enhanced_mock_bedrock_response

        weird_inputs = [
            "",
            "!@#$%^&*()",
            "a" * 500,
            "123456789",
            "नमस्ते",
            "Hello world I am a user",
        ]
        for inp in weird_inputs:
            try:
                result = _enhanced_mock_bedrock_response(inp, [])
                self.assertIn("next_question", result)
            except Exception as e:
                self.fail(f"Mock raised exception for input {inp!r}: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
