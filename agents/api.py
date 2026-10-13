"""
FastAPI REST API Server for Timi Stemi Risk Score.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from timi_stemi import calculate_metrics
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Timi Stemi Risk Score API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class TimiStemiRequest(BaseModel):
    age: int = Field(ge=0, le=120)
    diabetes_hypertension_angina: bool
    systolic_bp: float = Field(gt=0, le=400, allow_inf_nan=False)
    heart_rate: float = Field(gt=0, le=350, allow_inf_nan=False)
    killip_class: int = Field(ge=1, le=4)
    weight_kg: float = Field(gt=0, le=500, allow_inf_nan=False)
    anterior_st_elevation_or_lbbb: bool
    time_to_treatment_hours: float = Field(ge=0, le=1000, allow_inf_nan=False)


@app.post("/api/timi-stemi", tags=["Clinical score"])
def api_timi_stemi(payload: TimiStemiRequest):
    """Calculate the published 0–14 point TIMI STEMI score."""
    return calculate_metrics(**payload.model_dump())


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "timi-stemi-risk-score", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Keep the historical API routes above the static-files catch-all.
app.mount("/", StaticFiles(directory="web", html=True), name="static")
