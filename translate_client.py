"""
translate_client.py — Amazon Translate integration for Nyaaya.ai

Provides real-time translation between Hindi and English using AWS Translate.
Falls back to pass-through if AWS credentials are unavailable.
"""
from __future__ import annotations

from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import AWS_REGION, logger

# ---------------------------------------------------------------------------
# Supported language codes
# ---------------------------------------------------------------------------

LANG_MAP = {
    "hi": "hi",       # Hindi
    "en": "en",       # English
    "mr": "mr",       # Marathi
    "ta": "ta",       # Tamil
    "te": "te",       # Telugu
    "bn": "bn",       # Bengali
}

# ---------------------------------------------------------------------------
# Translate client (lazy singleton)
# ---------------------------------------------------------------------------

_translate_client = None


def _get_translate_client():
    global _translate_client
    if _translate_client is None:
        _translate_client = boto3.client(
            "translate",
            region_name=AWS_REGION,
        )
    return _translate_client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "hi",
) -> dict[str, Any]:
    """
    Translate text using Amazon Translate.

    Args:
        text: Input text to translate.
        source_lang: Source language code ("auto" for auto-detect).
        target_lang: Target language code.

    Returns:
        Dict with translated_text, source_language, target_language.
    """
    try:
        client = _get_translate_client()

        response = client.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang,
        )

        result = {
            "translated_text": response["TranslatedText"],
            "source_language": response["SourceLanguageCode"],
            "target_language": response["TargetLanguageCode"],
        }

        logger.info(
            "Translate: %s → %s (%d chars)",
            result["source_language"],
            result["target_language"],
            len(text),
        )
        return result

    except (BotoCoreError, ClientError) as e:
        logger.warning("Amazon Translate unavailable: %s — returning original text", str(e))
        return {
            "translated_text": text,
            "source_language": source_lang,
            "target_language": target_lang,
            "fallback": True,
        }

    except Exception as e:
        logger.exception("Unexpected translate error: %s", str(e))
        return {
            "translated_text": text,
            "source_language": source_lang,
            "target_language": target_lang,
            "fallback": True,
        }


def detect_language(text: str) -> str:
    """Detect dominant language using Amazon Comprehend."""
    try:
        comprehend = boto3.client("comprehend", region_name=AWS_REGION)
        response = comprehend.detect_dominant_language(Text=text)
        languages = response.get("Languages", [])
        if languages:
            return languages[0]["LanguageCode"]
        return "hi"
    except Exception:
        return "hi"
