"""
Pytest configuration and shared fixtures for timi-stemi-risk-score test suite.
"""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Set a deterministic test key for HMAC audit trail (never use in production)
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-secret-key-2026-fortestingonly")


import pytest
from agents.base import AuditLogger


@pytest.fixture(autouse=True)
def reset_audit_trail():
    """Reset the global audit trail before each test for isolation."""
    AuditLogger.reset()
    yield
    AuditLogger.reset()
