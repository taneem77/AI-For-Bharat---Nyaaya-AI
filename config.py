"""
config.py — AWS configuration, constants, and environment settings for Nyaaya.ai
"""
import os
import logging
from enum import Enum

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("nyaaya")

# ---------------------------------------------------------------------------
# AWS / Bedrock
# ---------------------------------------------------------------------------
AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")
BEDROCK_MODEL_ID: str = os.getenv(
    "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022"
)
DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "nyaaya_interviews")

# ---------------------------------------------------------------------------
# Application constants
# ---------------------------------------------------------------------------
MAX_INTERVIEW_TURNS: int = 15
CONTEXT_WINDOW_TURNS: int = 5          # last N turns sent to Bedrock
SESSION_TTL_SECONDS: int = 86_400      # 24 hours
MAX_TOKENS_BEDROCK: int = 500
INCOME_WARNING_THRESHOLD: int = 1_000_000

# ---------------------------------------------------------------------------
# Supported states (lowercase for comparison)
# ---------------------------------------------------------------------------
SUPPORTED_STATES: set[str] = {"maharashtra", "rajasthan", "uttar pradesh"}

# State name normalisation map (handle variations)
STATE_ALIASES: dict[str, str] = {
    "maharashtra": "Maharashtra",
    "rajasthan": "Rajasthan",
    "up": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
}

# ---------------------------------------------------------------------------
# Scheme IDs (canonical identifiers)
# ---------------------------------------------------------------------------
SCHEME_WIDOW_PENSION = "widow_pension_mh"
SCHEME_DISABILITY_ALLOWANCE = "disability_allowance"
SCHEME_NREGA = "nrega"

# ---------------------------------------------------------------------------
# Rate limiting (informational; enforcement via AWS WAF)
# ---------------------------------------------------------------------------
RATE_LIMIT_RPM: int = 100            # requests per minute per session_id

# ---------------------------------------------------------------------------
# Enums (shared across modules)
# ---------------------------------------------------------------------------

class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    WIDOW = "widow"
    DIVORCED = "divorced"
    SEPARATED = "separated"


class LifeEvent(str, Enum):
    WIDOW = "widow"
    DISABLED = "disabled"
    UNEMPLOYED = "unemployed"
    ELDERLY = "elderly"
    FARMER = "farmer"
    STUDENT = "student"
    NONE = "none"
