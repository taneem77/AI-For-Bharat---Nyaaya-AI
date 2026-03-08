# tests/conftest.py
"""Shared pytest configuration — adds project root to sys.path."""
import sys
import os

# Allow imports from project root (nyaaya_backend/) when running tests from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
