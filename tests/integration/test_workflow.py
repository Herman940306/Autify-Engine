"""
Autify Engine V1 — Integration Tests: Full Workflow
Tests the complete pipeline: Upload → Parse → Analysis → Draft → Approve/Reject.
Uses the FastAPI TestClient to simulate real HTTP requests.
"""

import os
import sys
import io
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from database.models import Base
from api.main import app, get_db


# ── Use in-memory SQLite for tests (avoids Windows file locking) ─────
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_test_engine)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_db():
    """Create fresh tables before each test using the in-memory engine."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────

def create_test_client(client):
    res = client.post("/clients", json={"name": "Test User", "email": "test@example.com"})
    assert res.status_code == 200
    return res.json()


def upload_csv(client, client_id):
    csv_content = b"product,revenue,units\nWidget,1000,10\nGadget,2000,15\nGizmo,1500,12\n"
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    res = client.post(f"/upload/{client_id}", files=files)
    assert res.status_code == 200
    return res.json()


# ── Full Workflow ─────────────────────────────────────────────────────

class TestFullWorkflow:
    def test_upload_creates_draft(self, client):
        """Upload → Parse → Analysis → Draft created with approved=False."""
        c = create_test_client(client)
        result = upload_csv(client, c["client_id"])

        assert "draft_id" in result
        assert result["message"] == "File processed, analysis ready, draft generated."

    def test_draft_starts_unapproved(self, client):
        """Verify the draft-only enforcement: new drafts are never approved."""
        c = create_test_client(client)
        upload = upload_csv(client, c["client_id"])

        draft_res = client.get(f"/drafts/{upload['draft_id']}")
        assert draft_res.status_code == 200
        draft = draft_res.json()
        assert draft["approved"] is False

    def test_approve_draft(self, client):
        """Human approves a draft — approved transitions to True."""
        c = create_test_client(client)
        upload = upload_csv(client, c["client_id"])

        approve_res = client.post(
            f"/drafts/{upload['draft_id']}/approve",
            json={"user_id": "AdminUser"},
        )
        assert approve_res.status_code == 200

        draft_res = client.get(f"/drafts/{upload['draft_id']}")
        assert draft_res.json()["approved"] is True

    def test_reject_draft_stays_unapproved(self, client):
        """Human rejects a draft — it remains unapproved and gets rejected flag."""
        c = create_test_client(client)
        upload = upload_csv(client, c["client_id"])

        reject_res = client.post(
            f"/drafts/{upload['draft_id']}/reject",
            json={"user_id": "AdminUser"},
        )
        assert reject_res.status_code == 200

        draft_res = client.get(f"/drafts/{upload['draft_id']}")
        draft_data = draft_res.json()
        assert draft_data["approved"] is False
        assert draft_data["rejected"] is True
        assert draft_data["rejected_at"] is not None

    def test_logs_created(self, client):
        """Verify append-only logs are written for draft creation and approval."""
        c = create_test_client(client)
        upload = upload_csv(client, c["client_id"])
        client.post(f"/drafts/{upload['draft_id']}/approve", json={"user_id": "Admin"})

        logs = client.get("/logs").json()
        actions = [l["action"] for l in logs]
        assert "draft_created_from_upload" in actions
        assert "approve" in actions

    def test_reject_creates_log(self, client):
        """Verify reject action is logged."""
        c = create_test_client(client)
        upload = upload_csv(client, c["client_id"])
        client.post(f"/drafts/{upload['draft_id']}/reject", json={"user_id": "Admin"})

        logs = client.get("/logs").json()
        actions = [l["action"] for l in logs]
        assert "reject" in actions

    def test_rejected_filter(self, client):
        """Verify ?status=rejected returns only rejected drafts."""
        c = create_test_client(client)
        u1 = upload_csv(client, c["client_id"])
        # Create a second client+draft so email is unique
        c2 = client.post("/clients", json={"name": "Second", "email": "second@test.com"}).json()
        u2 = upload_csv(client, c2["client_id"])

        # Reject first, approve second
        client.post(f"/drafts/{u1['draft_id']}/reject", json={"user_id": "Admin"})
        client.post(f"/drafts/{u2['draft_id']}/approve", json={"user_id": "Admin"})

        rejected = client.get("/drafts?status=rejected").json()
        approved = client.get("/drafts?status=approved").json()
        assert len(rejected) == 1
        assert rejected[0]["draft_id"] == u1["draft_id"]
        assert len(approved) == 1
        assert approved[0]["draft_id"] == u2["draft_id"]


# ── Dashboard Data Endpoints ─────────────────────────────────────────

class TestDashboardEndpoints:
    def test_summary(self, client):
        res = client.get("/analytics/summary")
        assert res.status_code == 200
        data = res.json()
        assert "total_clients" in data
        assert "pending_drafts" in data

    def test_notifications(self, client):
        c = create_test_client(client)
        upload_csv(client, c["client_id"])

        res = client.get("/notifications")
        assert res.status_code == 200
        notes = res.json()
        assert any(n["type"] == "pending_draft" for n in notes)

    def test_health(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "version" in data
