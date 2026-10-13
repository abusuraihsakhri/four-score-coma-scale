"""FastAPI REST application: clinical FOUR scoring and legacy workflow demo."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor
from four_score import calculate_metrics

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="FOUR Score API",
    description="Four-component coma assessment score plus separate nonclinical demo endpoints",
    version="3.1.0",
)


class FourScoreRequest(BaseModel):
    eye: int = Field(ge=0, le=4, strict=True)
    motor: int = Field(ge=0, le=4, strict=True)
    brainstem: int = Field(ge=0, le=4, strict=True)
    respiration: int = Field(ge=0, le=4, strict=True)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "four-score-coma-scale", "version": "3.1.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
    }


@app.post("/api/four-score")
def api_four_score(payload: FourScoreRequest):
    """Sum examined FOUR components; do not infer prognosis from score."""
    return calculate_metrics(**payload.model_dump())


@app.post("/api/audit", deprecated=True)
def api_audit(payload: SystemTaskPayload):
    """Legacy nonclinical threshold/audit demonstration, not a FOUR score."""
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException:
        raise HTTPException(status_code=422, detail="Disallowed sensitive identifier")


@app.post("/api/chat", deprecated=True)
def api_chat(req: ChatRequest):
    """Deterministic mock only; not a medical advisory service."""
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except SecurityException:
        raise HTTPException(status_code=422, detail="Disallowed sensitive identifier")


@app.get("/api/audit/logs", deprecated=True)
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
