"""
dynamodb_utils.py — DynamoDB operations for Nyaaya interview session persistence.

Provides:
- MockDynamoDBClient (in-memory, for local/testing use)
- RealDynamoDBClient (boto3, production)
- save_interview_state / load_interview_state (unified interface)
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from config import (
    AWS_REGION,
    DYNAMODB_TABLE_NAME,
    SESSION_TTL_SECONDS,
    logger,
)
from models import ConversationTurn, InterviewState, UserProfile

# ---------------------------------------------------------------------------
# Abstract base — enables dependency injection in tests
# ---------------------------------------------------------------------------

class DynamoDBInterface(ABC):

    @abstractmethod
    def put_item(self, item: dict[str, Any]) -> None: ...

    @abstractmethod
    def get_item(self, session_id: str) -> dict[str, Any] | None: ...


# ---------------------------------------------------------------------------
# Mock implementation (in-memory, zero AWS dependencies)
# ---------------------------------------------------------------------------

class MockDynamoDBClient(DynamoDBInterface):
    """Thread-safe in-memory DynamoDB mock for testing and local dev."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def put_item(self, item: dict[str, Any]) -> None:
        sid = item["session_id"]
        self._store[sid] = item
        logger.debug("MockDB PUT: session_id=%s", sid)

    def get_item(self, session_id: str) -> dict[str, Any] | None:
        item = self._store.get(session_id)
        if item is None:
            logger.debug("MockDB GET miss: session_id=%s", session_id)
            return None
        # Honour TTL
        if item.get("ttl", 0) < int(time.time()):
            del self._store[session_id]
            logger.debug("MockDB TTL expired: session_id=%s", session_id)
            return None
        logger.debug("MockDB GET hit: session_id=%s", session_id)
        return item

    def clear(self) -> None:
        """Test utility — wipe all state."""
        self._store.clear()


# ---------------------------------------------------------------------------
# Real boto3 implementation
# ---------------------------------------------------------------------------

class RealDynamoDBClient(DynamoDBInterface):
    """Production DynamoDB client (boto3)."""

    def __init__(
        self,
        table_name: str = DYNAMODB_TABLE_NAME,
        region: str = AWS_REGION,
    ) -> None:
        dynamodb = boto3.resource("dynamodb", region_name=region)
        self._table = dynamodb.Table(table_name)

    def put_item(self, item: dict[str, Any]) -> None:
        self._table.put_item(Item=item)
        logger.info("DynamoDB PUT: session_id=%s", item.get("session_id"))

    def get_item(self, session_id: str) -> dict[str, Any] | None:
        response = self._table.get_item(Key={"session_id": session_id})
        item = response.get("Item")
        if item is None:
            logger.info("DynamoDB GET miss: session_id=%s", session_id)
        return item


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _serialise_state(session_id: str, state: InterviewState) -> dict[str, Any]:
    """Convert InterviewState to a flat DynamoDB-ready dict."""
    history_payload = [
        {
            "turn": t.turn,
            "user_input": t.user_input,
            "assistant_response": t.assistant_response,
            "extracted_so_far": t.extracted_so_far,
        }
        for t in state.conversation_history
    ]
    profile_payload = (
        state.extracted_profile.model_dump(mode="json")
        if state.extracted_profile
        else None
    )
    return {
        "session_id": session_id,
        "timestamp": int(time.time()),
        "conversation_history": json.dumps(history_payload),
        "extracted_profile": json.dumps(profile_payload) if profile_payload else None,
        "interview_complete": state.interview_complete,
        "turn_count": state.turn_count,
        "ttl": int(time.time()) + SESSION_TTL_SECONDS,
    }


def _deserialise_state(session_id: str, item: dict[str, Any]) -> InterviewState:
    """Reconstruct InterviewState from DynamoDB item."""
    history_raw: list[dict] = json.loads(item.get("conversation_history", "[]"))
    history = [
        ConversationTurn(
            turn=h["turn"],
            user_input=h["user_input"],
            assistant_response=h["assistant_response"],
            extracted_so_far=h.get("extracted_so_far", {}),
        )
        for h in history_raw
    ]

    profile: UserProfile | None = None
    raw_profile = item.get("extracted_profile")
    if raw_profile:
        profile_dict = json.loads(raw_profile)
        if profile_dict:
            try:
                profile = UserProfile(**profile_dict)
            except Exception as exc:
                logger.warning("Could not reconstruct UserProfile: %s", exc)

    return InterviewState(
        user_id=session_id,
        conversation_history=history,
        extracted_profile=profile,
        interview_complete=bool(item.get("interview_complete", False)),
        turn_count=int(item.get("turn_count", len(history))),
        timestamp=datetime.now(timezone.utc),
        ttl=int(item.get("ttl", int(time.time()) + SESSION_TTL_SECONDS)),
    )


# ---------------------------------------------------------------------------
# Public API — used by main.py
# ---------------------------------------------------------------------------

def save_interview_state(
    session_id: str,
    state: InterviewState,
    db: DynamoDBInterface,
) -> None:
    """Persist interview state to DynamoDB (or mock)."""
    item = _serialise_state(session_id, state)
    db.put_item(item)


def load_interview_state(
    session_id: str,
    db: DynamoDBInterface,
) -> InterviewState | None:
    """
    Load interview state. Returns None if not found or TTL expired.
    """
    item = db.get_item(session_id)
    if item is None:
        return None
    return _deserialise_state(session_id, item)
