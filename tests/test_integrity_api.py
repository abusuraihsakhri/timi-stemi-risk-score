"""Tests for authenticated HMAC chains and score API payloads."""
from agents.base import AuditTrail
from agents.api import TimiStemiRequest, api_timi_stemi


def test_audit_detects_entry_tampering():
    audit = AuditTrail(secret_key="unit-test-only-key-with-sufficient-entropy")
    audit.log("worker", "test", "SCORE", {"result": "ok"})
    audit.log("worker", "test", "SCORE", {"result": "ok"})
    assert audit.verify_integrity()
    snapshot = audit.get_trail()
    snapshot[0]["actor"] = "changed"
    assert audit.verify_integrity()  # Returned snapshots are not mutable storage
    audit.logs[-1]["actor"] = "changed"
    assert not audit.verify_integrity()


def test_api_score_matches_original_points():
    model = TimiStemiRequest(
        age=75, diabetes_hypertension_angina=True, systolic_bp=90,
        heart_rate=110, killip_class=2, weight_kg=60,
        anterior_st_elevation_or_lbbb=True, time_to_treatment_hours=5,
    )
    response = api_timi_stemi(model)
    assert response["score"] == 14
    assert response["mortality_30_day_percent"] == 35.9
