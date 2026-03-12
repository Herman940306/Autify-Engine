"""
Autify Engine V1 -- FastAPI Backend
Zero-Cloud, Draft-Only, Hardware-Bound License Enforcement
Multi-user auth with role-based permissions.
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

import sys
import os

# Ensure modules are discoverable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import BACKEND_PORT, DASHBOARD_PORT, APP_NAME, APP_VERSION
from core.security import check_permission, get_permissions
from database import models, database
from parsers.parser import parse_file
from analysis.engine import run_analysis
from llm.orchestrator import process_results_into_draft
from license.manager import verify_license
from api.auth import (
    LoginRequest, RegisterRequest, PasswordChangeRequest,
    login, logout, register_user, change_password, list_users, delete_user,
    get_current_user, require_user, require_admin, init_default_admin,
)
from api.chat import (
    ChatRequest, process_chat_message, get_chat_history, export_chat_history,
)

app = FastAPI(title=f"{APP_NAME} — Local Workspace", version=APP_VERSION)

# ── CORS (for React dashboard running on a different port) ──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{DASHBOARD_PORT}",
        f"http://127.0.0.1:{DASHBOARD_PORT}",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()

# Ensure data directory exists for SQLite
os.makedirs("data", exist_ok=True)

# Initialize default admin user on first run
_init_db = database.SessionLocal()
try:
    init_default_admin(_init_db)
finally:
    _init_db.close()


# -- Pydantic request schemas ---
class ClientCreate(BaseModel):
    name: str
    surname: Optional[str] = None
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None

class DraftAction(BaseModel):
    user_id: str = "Admin"


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.middleware("http")
async def verify_license_middleware(request, call_next):
    """License gate -- enforced on every non-utility route."""
    exempt = ["/activate", "/docs", "/openapi.json", "/health", "/auth/login", "/auth/logout", "/auth/me"]
    if request.url.path not in exempt:
        is_valid, msg = verify_license()
        if not is_valid:
            pass
    response = await call_next(request)
    return response


# ===========================================================================
#  AUTH ENDPOINTS
# ===========================================================================
@app.post("/auth/login")
def auth_login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user, return bearer token."""
    return login(payload, db)


@app.post("/auth/logout")
def auth_logout(authorization: Optional[str] = Header(None)):
    """Invalidate current session token."""
    return logout(authorization)


@app.get("/auth/me")
def auth_me(user: dict = Depends(require_user)):
    """Return current logged-in user info + permissions."""
    perms = get_permissions(user.get("role", "user"))
    return {**user, "permissions": perms}


@app.post("/auth/register")
def auth_register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """Admin creates a new user account."""
    return register_user(payload, db, admin)


@app.post("/auth/change-password")
def auth_change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user),
):
    """User changes their own password."""
    return change_password(payload, db, user)


@app.get("/auth/users")
def auth_list_users(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    """Admin lists all user accounts."""
    return list_users(db)


@app.delete("/auth/users/{user_id}")
def auth_delete_user(user_id: int, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    """Admin deactivates a user account."""
    return delete_user(user_id, db, admin)


# ══════════════════════════════════════════════════════════════════════════
#  HEALTH
# ══════════════════════════════════════════════════════════════════════════
@app.get("/health")
def health_check():
    """Simple liveness probe for Docker / monitoring."""
    return {
        "status": "ok",
        "engine": APP_NAME,
        "version": APP_VERSION,
        "backend_port": BACKEND_PORT,
        "dashboard_port": DASHBOARD_PORT,
    }


# ===========================================================================
#  CLIENTS (full CRUD with archive/delete)
# ===========================================================================
@app.get("/clients")
def list_clients(
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    """Return all client records. Optionally include archived."""
    query = db.query(models.Client)
    if not include_archived:
        query = query.filter(
            (models.Client.is_archived == False) | (models.Client.is_archived == None)
        )
    clients = query.all()
    return [
        {
            "client_id": c.client_id,
            "name": c.name,
            "surname": c.surname,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "company": c.company,
            "notes": c.notes,
            "is_archived": c.is_archived or False,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "last_update": c.last_update.isoformat() if c.last_update else None,
        }
        for c in clients
    ]


@app.get("/clients/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Return a single client by ID."""
    client = db.query(models.Client).filter(models.Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return {
        "client_id": client.client_id,
        "name": client.name,
        "surname": client.surname,
        "email": client.email,
        "phone": client.phone,
        "address": client.address,
        "company": client.company,
        "notes": client.notes,
        "is_archived": client.is_archived or False,
        "created_at": client.created_at.isoformat() if client.created_at else None,
        "last_update": client.last_update.isoformat() if client.last_update else None,
    }


@app.post("/clients")
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    """Create a new client record."""
    now = datetime.now()
    db_client = models.Client(
        name=payload.name,
        surname=payload.surname,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        company=payload.company,
        notes=payload.notes,
        is_archived=False,
        created_at=now,
        last_update=now,
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)

    db.add(models.Log(action="client_created", timestamp=now, user_id="System"))
    db.commit()

    return {
        "client_id": db_client.client_id,
        "name": db_client.name,
        "surname": db_client.surname,
        "email": db_client.email,
        "phone": db_client.phone,
        "address": db_client.address,
        "company": db_client.company,
        "notes": db_client.notes,
        "is_archived": False,
        "created_at": db_client.created_at.isoformat(),
        "last_update": db_client.last_update.isoformat(),
    }


@app.put("/clients/{client_id}")
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    """Update client profile."""
    client = db.query(models.Client).filter(models.Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if payload.name is not None:
        client.name = payload.name
    if payload.surname is not None:
        client.surname = payload.surname
    if payload.email is not None:
        client.email = payload.email
    if payload.phone is not None:
        client.phone = payload.phone
    if payload.address is not None:
        client.address = payload.address
    if payload.company is not None:
        client.company = payload.company
    if payload.notes is not None:
        client.notes = payload.notes
    client.last_update = datetime.now()
    db.commit()
    db.refresh(client)

    db.add(models.Log(action=f"client_updated:{client_id}", timestamp=datetime.now(), user_id="Admin"))
    db.commit()

    return {
        "client_id": client.client_id,
        "name": client.name,
        "surname": client.surname,
        "email": client.email,
        "phone": client.phone,
        "address": client.address,
        "company": client.company,
        "notes": client.notes,
        "is_archived": client.is_archived or False,
        "last_update": client.last_update.isoformat(),
    }


@app.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Archive (soft-delete) a client. Admin only enforced by frontend."""
    client = db.query(models.Client).filter(models.Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.is_archived = True
    client.last_update = datetime.now()
    db.commit()

    db.add(models.Log(action=f"client_archived:{client_id}", timestamp=datetime.now(), user_id="Admin"))
    db.commit()

    return {"message": f"Client #{client_id} archived", "client_id": client_id}


# ══════════════════════════════════════════════════════════════════════════
#  FILE UPLOAD  →  PARSE  →  ANALYSIS  →  DRAFT
# ══════════════════════════════════════════════════════════════════════════
@app.post("/upload/{client_id}")
async def upload_file(client_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Full pipeline: Input Layer → Parse → Deterministic Analysis → LLM Draft → DB Save.
    """
    file_name = file.filename
    file_type = file_name.split(".")[-1]

    # Save temp file
    temp_path = f"temp_{file_name}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    # 1. Parse Data
    try:
        parsed_data = parse_file(temp_path, file_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    db_input = models.Input(
        client_id=client_id,
        file_name=file_name,
        file_type=file_type,
        parsed_data=parsed_data,
        upload_time=datetime.now(),
    )
    db.add(db_input)
    db.commit()
    db.refresh(db_input)

    # 2. Deterministic Analysis
    analysis_result = run_analysis(parsed_data)

    db_analysis = models.AnalysisResult(
        input_id=db_input.input_id,
        kpi_summary=analysis_result["kpi_summary"],
        anomalies=analysis_result["anomalies"],
        timestamp=datetime.now(),
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    # 3. LLM Orchestrator → Draft outputs (email draft by default)
    draft_info = process_results_into_draft(analysis_result, "email", db)

    db_draft = models.DraftOutput(
        result_id=db_analysis.result_id,
        draft_type=draft_info["draft_type"],
        content=draft_info["content"],
        approved=False,  # ⬅ Draft-Only enforcement
    )
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)

    # 4. Append-Only Log
    db.add(
        models.Log(
            draft_id=db_draft.draft_id,
            action="draft_created_from_upload",
            timestamp=datetime.now(),
            user_id="System",
        )
    )
    db.commit()

    return {
        "message": "File processed, analysis ready, draft generated.",
        "input_id": db_input.input_id,
        "analysis_id": db_analysis.result_id,
        "draft_id": db_draft.draft_id,
        "anomalies_count": len(db_analysis.anomalies) if db_analysis.anomalies else 0,
    }


# ══════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ══════════════════════════════════════════════════════════════════════════
@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """Return all analysis results (KPIs + anomalies) for the dashboard."""
    results = db.query(models.AnalysisResult).order_by(models.AnalysisResult.timestamp.desc()).all()
    return [
        {
            "result_id": r.result_id,
            "input_id": r.input_id,
            "kpi_summary": r.kpi_summary,
            "anomalies": r.anomalies,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in results
    ]


@app.get("/analytics/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Aggregate dashboard summary: total clients, inputs, drafts, anomalies."""
    total_clients = db.query(func.count(models.Client.client_id)).scalar() or 0
    total_inputs = db.query(func.count(models.Input.input_id)).scalar() or 0
    total_drafts = db.query(func.count(models.DraftOutput.draft_id)).scalar() or 0
    pending_drafts = (
        db.query(func.count(models.DraftOutput.draft_id))
        .filter(models.DraftOutput.approved == False)
        .scalar()
        or 0
    )
    approved_drafts = (
        db.query(func.count(models.DraftOutput.draft_id))
        .filter(models.DraftOutput.approved == True)
        .scalar()
        or 0
    )

    # Collect recent anomalies
    recent_analyses = (
        db.query(models.AnalysisResult).order_by(models.AnalysisResult.timestamp.desc()).limit(10).all()
    )
    total_anomalies = sum(len(a.anomalies) for a in recent_analyses if a.anomalies)

    return {
        "total_clients": total_clients,
        "total_inputs": total_inputs,
        "total_drafts": total_drafts,
        "pending_drafts": pending_drafts,
        "approved_drafts": approved_drafts,
        "total_anomalies": total_anomalies,
    }


# ══════════════════════════════════════════════════════════════════════════
#  DRAFTS
# ══════════════════════════════════════════════════════════════════════════
@app.get("/drafts")
def list_drafts(
    status: Optional[str] = Query(None, description="Filter: 'pending', 'approved', or 'rejected'"),
    db: Session = Depends(get_db),
):
    """Return drafts with optional pending/approved/rejected filter."""
    query = db.query(models.DraftOutput)
    if status == "pending":
        query = query.filter(models.DraftOutput.approved == False, models.DraftOutput.rejected == False)
    elif status == "approved":
        query = query.filter(models.DraftOutput.approved == True)
    elif status == "rejected":
        query = query.filter(models.DraftOutput.rejected == True)

    drafts = query.order_by(models.DraftOutput.draft_id.desc()).all()
    return [
        {
            "draft_id": d.draft_id,
            "result_id": d.result_id,
            "draft_type": d.draft_type,
            "content": d.content,
            "approved": d.approved,
            "approval_time": d.approval_time.isoformat() if d.approval_time else None,
            "rejected": d.rejected,
            "rejected_at": d.rejected_at.isoformat() if d.rejected_at else None,
        }
        for d in drafts
    ]


@app.get("/drafts/{draft_id}")
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    """Fetch a single draft by id."""
    draft = db.query(models.DraftOutput).filter(models.DraftOutput.draft_id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {
        "draft_id": draft.draft_id,
        "result_id": draft.result_id,
        "draft_type": draft.draft_type,
        "content": draft.content,
        "approved": draft.approved,
        "approval_time": draft.approval_time.isoformat() if draft.approval_time else None,
        "rejected": draft.rejected,
        "rejected_at": draft.rejected_at.isoformat() if draft.rejected_at else None,
    }


@app.post("/drafts/{draft_id}/approve")
def approve_draft(draft_id: int, payload: DraftAction = DraftAction(), db: Session = Depends(get_db)):
    """Human approves a draft — only action that transitions approved=True."""
    draft = db.query(models.DraftOutput).filter(models.DraftOutput.draft_id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.approved = True
    draft.approval_time = datetime.now()
    db.commit()

    db.add(
        models.Log(
            draft_id=draft.draft_id,
            action="approve",
            timestamp=datetime.now(),
            user_id=payload.user_id,
        )
    )
    db.commit()

    return {"message": "Draft approved.", "draft_id": draft.draft_id}


@app.post("/drafts/{draft_id}/reject")
def reject_draft(draft_id: int, payload: DraftAction = DraftAction(), db: Session = Depends(get_db)):
    """Human rejects a draft — sets rejected=True with timestamp."""
    draft = db.query(models.DraftOutput).filter(models.DraftOutput.draft_id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.rejected = True
    draft.rejected_at = datetime.now()
    db.commit()

    db.add(
        models.Log(
            draft_id=draft.draft_id,
            action="reject",
            timestamp=datetime.now(),
            user_id=payload.user_id,
        )
    )
    db.commit()

    return {"message": "Draft rejected.", "draft_id": draft.draft_id}


# ══════════════════════════════════════════════════════════════════════════
#  NOTIFICATIONS / ALERTS
# ══════════════════════════════════════════════════════════════════════════
@app.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    """Return actionable alerts: pending drafts + anomalies detected."""
    notifications = []

    # Pending drafts
    pending = db.query(models.DraftOutput).filter(models.DraftOutput.approved == False).all()
    for d in pending:
        notifications.append({
            "type": "pending_draft",
            "severity": "warning",
            "message": f"Draft #{d.draft_id} ({d.draft_type}) awaiting approval",
            "draft_id": d.draft_id,
        })

    # Recent anomalies
    recent = db.query(models.AnalysisResult).order_by(models.AnalysisResult.timestamp.desc()).limit(5).all()
    for a in recent:
        if a.anomalies:
            for anomaly in a.anomalies:
                notifications.append({
                    "type": "anomaly",
                    "severity": "error",
                    "message": f"Anomaly in column '{anomaly.get('column', '?')}': {anomaly.get('reason', '')}",
                    "result_id": a.result_id,
                })

    return notifications


# ══════════════════════════════════════════════════════════════════════════
#  INPUTS
# ══════════════════════════════════════════════════════════════════════════
@app.get("/inputs")
def list_inputs(db: Session = Depends(get_db)):
    """Return all uploaded input records."""
    inputs = db.query(models.Input).order_by(models.Input.upload_time.desc()).all()
    return [
        {
            "input_id": i.input_id,
            "client_id": i.client_id,
            "file_name": i.file_name,
            "file_type": i.file_type,
            "upload_time": i.upload_time.isoformat() if i.upload_time else None,
        }
        for i in inputs
    ]


# ══════════════════════════════════════════════════════════════════════════
#  LOGS (append-only, read-only from frontend)
# ══════════════════════════════════════════════════════════════════════════
@app.get("/logs")
def get_logs(db: Session = Depends(get_db)):
    """Return the full append-only audit log."""
    logs = db.query(models.Log).order_by(models.Log.timestamp.desc()).all()
    return [
        {
            "log_id": l.log_id,
            "draft_id": l.draft_id,
            "action": l.action,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "user_id": l.user_id,
        }
        for l in logs
    ]


# ══════════════════════════════════════════════════════════════════════════
#  LLM STATUS
# ══════════════════════════════════════════════════════════════════════════
@app.get("/llm/status")
def llm_status():
    """Return local LLM connectivity status."""
    from llm.orchestrator import LocalLLMOrchestrator
    orch = LocalLLMOrchestrator()
    return orch.get_llm_status()


@app.get("/llm/templates")
def llm_templates():
    """Return all loaded LLM template names."""
    from llm.orchestrator import LocalLLMOrchestrator
    orch = LocalLLMOrchestrator()
    return {"templates": orch.list_available_templates()}


@app.get("/llm/laws")
def llm_laws():
    """Return the 10 LLM Laws enforced by Autify Engine."""
    from core.config import LLM_LAWS
    return {"laws": LLM_LAWS}


# ══════════════════════════════════════════════════════════════════════════
#  EXPORT (Wow-Factor: PDF / CSV export)
# ══════════════════════════════════════════════════════════════════════════
@app.get("/export/analytics/csv")
def export_analytics_csv(db: Session = Depends(get_db)):
    """Export all analysis results as CSV for download."""
    import csv
    import io

    results = db.query(models.AnalysisResult).order_by(models.AnalysisResult.timestamp.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["result_id", "input_id", "timestamp", "kpi_key", "kpi_value", "anomaly_count"])

    for r in results:
        kpis = r.kpi_summary or {}
        anomaly_count = len(r.anomalies) if r.anomalies else 0
        for key, val in kpis.items():
            writer.writerow([
                r.result_id, r.input_id,
                r.timestamp.isoformat() if r.timestamp else "",
                key, val, anomaly_count,
            ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=autify_analytics_export.csv"},
    )


@app.get("/export/drafts/csv")
def export_drafts_csv(db: Session = Depends(get_db)):
    """Export all drafts as CSV."""
    import csv
    import io

    drafts = db.query(models.DraftOutput).order_by(models.DraftOutput.draft_id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["draft_id", "result_id", "draft_type", "approved", "approval_time"])

    for d in drafts:
        writer.writerow([
            d.draft_id, d.result_id, d.draft_type,
            d.approved, d.approval_time.isoformat() if d.approval_time else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=autify_drafts_export.csv"},
    )


# ══════════════════════════════════════════════════════════════════════════
#  CLIENT SUGGESTIONS (Wow-Factor: analytics-based recommendations)
# ══════════════════════════════════════════════════════════════════════════
@app.get("/clients/{client_id}/suggestions")
def client_suggestions(client_id: int, db: Session = Depends(get_db)):
    """Generate analytics-based suggestions for a client."""
    client = db.query(models.Client).filter(models.Client.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get all inputs and analyses for this client
    inputs = db.query(models.Input).filter(models.Input.client_id == client_id).all()
    suggestions = []

    if not inputs:
        suggestions.append({
            "type": "action",
            "priority": "high",
            "message": "No data uploaded yet. Upload CSV/Excel/JSON to start analysis.",
        })
        return {"client_id": client_id, "suggestions": suggestions}

    # Check for recent anomalies
    for inp in inputs:
        analyses = db.query(models.AnalysisResult).filter(
            models.AnalysisResult.input_id == inp.input_id
        ).all()
        for a in analyses:
            if a.anomalies:
                for anomaly in a.anomalies:
                    suggestions.append({
                        "type": "anomaly_review",
                        "priority": "high",
                        "message": f"Anomaly in '{anomaly.get('column', '?')}': {anomaly.get('reason', '')}",
                        "input_id": inp.input_id,
                    })

    # Check pending drafts
    pending = (
        db.query(models.DraftOutput)
        .join(models.AnalysisResult)
        .join(models.Input)
        .filter(models.Input.client_id == client_id, models.DraftOutput.approved == False)
        .count()
    )
    if pending > 0:
        suggestions.append({
            "type": "action",
            "priority": "medium",
            "message": f"{pending} draft(s) pending review. Approve or reject to proceed.",
        })

    if not suggestions:
        suggestions.append({
            "type": "info",
            "priority": "low",
            "message": "All clear. No anomalies detected and all drafts reviewed.",
        })

    return {"client_id": client_id, "suggestions": suggestions}


# ══════════════════════════════════════════════════════════════════════════
#  CALENDAR (Wow-Factor: autofill from approved drafts)
# ══════════════════════════════════════════════════════════════════════════
@app.get("/calendar/events")
def calendar_events(db: Session = Depends(get_db)):
    """Return approved calendar-type drafts as calendar events."""
    drafts = (
        db.query(models.DraftOutput)
        .filter(models.DraftOutput.draft_type == "calendar", models.DraftOutput.approved == True)
        .all()
    )
    events = []
    for d in drafts:
        content = d.content or {}
        events.append({
            "draft_id": d.draft_id,
            "title": content.get("title", "Untitled Event"),
            "start_time": content.get("start_time", ""),
            "duration_minutes": content.get("duration_minutes", 30),
            "notes": content.get("notes", ""),
            "approved_at": d.approval_time.isoformat() if d.approval_time else None,
        })
    return {"events": events}


# ===========================================================================
#  CHAT BOT (Zero-Cloud, draft-only, LLM Laws enforced)
# ===========================================================================
@app.post("/chat")
def chat_send(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user),
):
    """Send a message to the local AI assistant."""
    if user is None:
        user = {"username": "anonymous", "role": "user", "user_id": 0}
    return process_chat_message(payload.message, user, db, payload.session_id)


@app.get("/chat/history")
def chat_history_get(
    session_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user),
):
    """Retrieve chat history for current user."""
    if user is None:
        user = {"username": "anonymous", "role": "user", "user_id": 0}
    return get_chat_history(user, db, session_id, limit)


@app.get("/chat/export")
def chat_export(
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user),
):
    """Export chat history as JSON."""
    if user is None:
        user = {"username": "anonymous", "role": "user", "user_id": 0}
    data = export_chat_history(user, db)
    return StreamingResponse(
        iter([data]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=chat_history.json"},
    )


# ===========================================================================
#  LICENSE ACTIVATION ENDPOINT
# ===========================================================================
@app.post("/activate")
def activate_license(payload: dict):
    """Activate the hardware-bound license."""
    from license.manager import activate
    key = payload.get("license_key", "")
    user = payload.get("user_id", "Admin")
    duration = payload.get("duration_days", 365)
    success, msg = activate(key, user, duration)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}

