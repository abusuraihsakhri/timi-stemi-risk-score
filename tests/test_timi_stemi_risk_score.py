"""
Automated Pytest Test Suite for Timi Stemi Risk Score.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, AuditTrail
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_guard_ssn_detection():
    """Test PHI guard detects SSN patterns."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")


def test_phi_guard_phone_detection():
    """Test PHI guard detects phone number patterns."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Contact patient at 555-123-4567")


def test_phi_guard_email_detection():
    """Test PHI guard detects email addresses."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Email results to patient@hospital.com")


def test_phi_redaction():
    """Test PHI redaction replaces sensitive data."""
    redacted = PHIGuard.redact_phi("Patient MRN-12345678 has results")
    assert "MRN-12345678" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_audit_trail_requires_secret_key():
    """Test that AuditTrail raises error when no secret key is provided."""
    original_key = os.environ.pop("AUDIT_SECRET_KEY", None)
    try:
        with pytest.raises(SecurityException, match="AUDIT_SECRET_KEY"):
            AuditTrail()
    finally:
        if original_key:
            os.environ["AUDIT_SECRET_KEY"] = original_key


def test_audit_trail_weak_key_rejected():
    """Test that AuditTrail rejects weak/short secret keys."""
    with pytest.raises(SecurityException, match="at least 16 characters"):
        AuditTrail(secret_key="short")


def test_audit_trail_chaining():
    """Test that audit trail entries are cryptographically chained."""
    trail = AuditTrail(secret_key="test-key-for-chaining-validation-2026")
    trail.log("test_actor", "test_tier", "TEST_EVENT", {"data": "value1"})
    trail.log("test_actor", "test_tier", "TEST_EVENT", {"data": "value2"})

    logs = trail.get_trail()
    assert len(logs) == 2
    # Second entry's prev_hash should equal first entry's current_hash
    assert logs[1]["prev_hash"] == logs[0]["current_hash"]
    assert trail.verify_integrity() is True


def test_supervisor_blocks_phi_in_task_id():
    """Test that supervisor rejects PHI in task identifiers."""
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="Patient MRN-12345678",
        target_identifier="KEY-01",
        primary_metric=10.0,
    )
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)
