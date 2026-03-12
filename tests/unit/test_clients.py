"""
Autify Engine V1 -- QA Tests: Client CRUD Operations
Tests create, read, update, delete (archive), and expanded fields.
"""

import os
import sys
import pytest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Client, Log


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def db_session(tmp_path):
    """Fresh in-memory DB per test."""
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_client(db_session):
    """Create a sample client."""
    client = Client(
        name="Test Corp",
        surname="Smith",
        email="test@corp.com",
        phone="+27 11 555 0100",
        address="123 Main Street, Johannesburg",
        company="Test Corporation",
        notes="Initial notes",
        is_archived=False,
        created_at=datetime.now(),
        last_update=datetime.now(),
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client


# ── Client Model ──────────────────────────────────────────────────────

class TestClientModel:
    def test_client_has_all_fields(self, sample_client):
        assert sample_client.name == "Test Corp"
        assert sample_client.surname == "Smith"
        assert sample_client.email == "test@corp.com"
        assert sample_client.phone == "+27 11 555 0100"
        assert sample_client.address == "123 Main Street, Johannesburg"
        assert sample_client.company == "Test Corporation"
        assert sample_client.notes == "Initial notes"
        assert sample_client.is_archived is False
        assert sample_client.created_at is not None

    def test_client_optional_fields(self, db_session):
        """Phone, company, notes, surname, address are optional."""
        client = Client(
            name="Minimal",
            email="min@test.com",
            last_update=datetime.now(),
        )
        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)
        assert client.phone is None
        assert client.company is None
        assert client.notes is None
        assert client.surname is None
        assert client.address is None
        assert client.is_archived is None or client.is_archived is False

    def test_email_unique_constraint(self, db_session, sample_client):
        dupe = Client(name="Dupe", email="test@corp.com", last_update=datetime.now())
        db_session.add(dupe)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


# ── Create ────────────────────────────────────────────────────────────

class TestClientCreate:
    def test_create_client_basic(self, db_session):
        client = Client(name="New Client", email="new@test.com", last_update=datetime.now())
        db_session.add(client)
        db_session.commit()
        assert client.client_id is not None
        assert client.client_id > 0

    def test_create_client_with_all_fields(self, db_session):
        client = Client(
            name="Full Client",
            surname="van der Berg",
            email="full@test.com",
            phone="012-345-6789",
            address="456 Oak Avenue, Cape Town",
            company="Full Corp Ltd",
            notes="Important client",
            is_archived=False,
            created_at=datetime.now(),
            last_update=datetime.now(),
        )
        db_session.add(client)
        db_session.commit()
        fetched = db_session.query(Client).filter(Client.email == "full@test.com").first()
        assert fetched.name == "Full Client"
        assert fetched.surname == "van der Berg"
        assert fetched.phone == "012-345-6789"
        assert fetched.address == "456 Oak Avenue, Cape Town"
        assert fetched.company == "Full Corp Ltd"
        assert fetched.notes == "Important client"


# ── Read ──────────────────────────────────────────────────────────────

class TestClientRead:
    def test_read_client_by_id(self, db_session, sample_client):
        fetched = db_session.query(Client).filter(Client.client_id == sample_client.client_id).first()
        assert fetched is not None
        assert fetched.name == "Test Corp"

    def test_read_all_clients(self, db_session, sample_client):
        # Add another
        db_session.add(Client(name="Second", email="second@test.com", last_update=datetime.now()))
        db_session.commit()
        clients = db_session.query(Client).all()
        assert len(clients) >= 2

    def test_filter_excludes_archived(self, db_session, sample_client):
        # Archive the sample client
        sample_client.is_archived = True
        db_session.commit()
        active = db_session.query(Client).filter(
            (Client.is_archived == False) | (Client.is_archived == None)
        ).all()
        archived_ids = [c.client_id for c in active]
        assert sample_client.client_id not in archived_ids

    def test_filter_includes_archived_when_asked(self, db_session, sample_client):
        sample_client.is_archived = True
        db_session.commit()
        all_clients = db_session.query(Client).all()
        assert any(c.client_id == sample_client.client_id for c in all_clients)


# ── Update ────────────────────────────────────────────────────────────

class TestClientUpdate:
    def test_update_name(self, db_session, sample_client):
        sample_client.name = "Updated Corp"
        sample_client.last_update = datetime.now()
        db_session.commit()
        fetched = db_session.query(Client).filter(Client.client_id == sample_client.client_id).first()
        assert fetched.name == "Updated Corp"

    def test_update_email(self, db_session, sample_client):
        sample_client.email = "updated@corp.com"
        db_session.commit()
        db_session.refresh(sample_client)
        assert sample_client.email == "updated@corp.com"

    def test_update_optional_fields(self, db_session, sample_client):
        sample_client.phone = "+27 21 555 9999"
        sample_client.company = "New Company Name"
        sample_client.notes = "Updated notes"
        sample_client.surname = "Johnson"
        sample_client.address = "789 New Road, Pretoria"
        db_session.commit()
        db_session.refresh(sample_client)
        assert sample_client.phone == "+27 21 555 9999"
        assert sample_client.company == "New Company Name"
        assert sample_client.notes == "Updated notes"
        assert sample_client.surname == "Johnson"
        assert sample_client.address == "789 New Road, Pretoria"

    def test_partial_update_preserves_other_fields(self, db_session, sample_client):
        original_email = sample_client.email
        sample_client.name = "Only Name Changed"
        db_session.commit()
        db_session.refresh(sample_client)
        assert sample_client.email == original_email
        assert sample_client.phone == "+27 11 555 0100"


# ── Delete (Archive) ─────────────────────────────────────────────────

class TestClientDelete:
    def test_archive_client(self, db_session, sample_client):
        """Delete = soft archive, not physical removal."""
        sample_client.is_archived = True
        sample_client.last_update = datetime.now()
        db_session.commit()
        db_session.refresh(sample_client)
        assert sample_client.is_archived is True
        # Client still exists in DB
        fetched = db_session.query(Client).filter(Client.client_id == sample_client.client_id).first()
        assert fetched is not None

    def test_archived_client_excluded_from_active(self, db_session, sample_client):
        sample_client.is_archived = True
        db_session.commit()
        active = db_session.query(Client).filter(
            (Client.is_archived == False) | (Client.is_archived == None)
        ).all()
        assert all(c.client_id != sample_client.client_id for c in active)

    def test_multiple_archives(self, db_session):
        """Can archive multiple clients."""
        c1 = Client(name="A", email="a@test.com", is_archived=True, last_update=datetime.now())
        c2 = Client(name="B", email="b@test.com", is_archived=True, last_update=datetime.now())
        c3 = Client(name="C", email="c@test.com", is_archived=False, last_update=datetime.now())
        db_session.add_all([c1, c2, c3])
        db_session.commit()
        active = db_session.query(Client).filter(
            (Client.is_archived == False) | (Client.is_archived == None)
        ).all()
        active_names = [c.name for c in active]
        assert "C" in active_names
        assert "A" not in active_names
        assert "B" not in active_names
