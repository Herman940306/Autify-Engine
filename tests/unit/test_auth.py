"""
Autify Engine V1 -- QA Tests: Authentication & User Management
Tests login, registration, token management, password change,
role-based access, and default admin initialization.
"""

import os
import sys
import pytest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, User, Log
from api.auth import (
    _hash_password,
    _verify_password,
    login,
    logout,
    register_user,
    change_password,
    list_users,
    delete_user,
    init_default_admin,
    LoginRequest,
    RegisterRequest,
    PasswordChangeRequest,
    _active_tokens,
)
from core.security import get_permissions, has_permission, check_permission, ROLES


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


@pytest.fixture(autouse=True)
def clear_tokens():
    """Clear token store before each test."""
    _active_tokens.clear()
    yield
    _active_tokens.clear()


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    pw_hash, _ = _hash_password("secureadmin")
    user = User(
        username="testadmin",
        password_hash=pw_hash,
        role="admin",
        display_name="Test Admin",
        created_at=datetime.now(),
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session):
    """Create a regular user for testing."""
    pw_hash, _ = _hash_password("userpass123")
    user = User(
        username="testuser",
        password_hash=pw_hash,
        role="user",
        display_name="Test User",
        created_at=datetime.now(),
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ── Password Hashing ─────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_password_returns_salt_and_hash(self):
        result, salt = _hash_password("mypassword")
        assert "$" in result
        assert len(salt) == 32  # hex 16 bytes

    def test_same_password_different_salts(self):
        h1, _ = _hash_password("same")
        h2, _ = _hash_password("same")
        assert h1 != h2  # random salt each time

    def test_verify_correct_password(self):
        stored, _ = _hash_password("correct")
        assert _verify_password("correct", stored) is True

    def test_verify_wrong_password(self):
        stored, _ = _hash_password("correct")
        assert _verify_password("wrong", stored) is False

    def test_verify_malformed_hash(self):
        assert _verify_password("any", "nohashhere") is False


# ── Login ─────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, db_session, admin_user):
        result = login(LoginRequest(username="testadmin", password="secureadmin"), db_session)
        assert "token" in result
        assert result["user"]["username"] == "testadmin"
        assert result["user"]["role"] == "admin"

    def test_login_returns_must_change_password(self, db_session):
        pw_hash, _ = _hash_password("temppass")
        user = User(
            username="newadmin", password_hash=pw_hash, role="admin",
            created_at=datetime.now(), is_active=True, must_change_password=True,
        )
        db_session.add(user)
        db_session.commit()
        result = login(LoginRequest(username="newadmin", password="temppass"), db_session)
        assert result["user"]["must_change_password"] is True

    def test_login_wrong_password(self, db_session, admin_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            login(LoginRequest(username="testadmin", password="wrongpass"), db_session)
        assert exc.value.status_code == 401

    def test_login_nonexistent_user(self, db_session):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            login(LoginRequest(username="nobody", password="any"), db_session)
        assert exc.value.status_code == 401

    def test_login_inactive_user(self, db_session):
        from fastapi import HTTPException
        pw_hash, _ = _hash_password("pass")
        user = User(
            username="inactive", password_hash=pw_hash, role="user",
            created_at=datetime.now(), is_active=False, must_change_password=False,
        )
        db_session.add(user)
        db_session.commit()
        with pytest.raises(HTTPException) as exc:
            login(LoginRequest(username="inactive", password="pass"), db_session)
        assert exc.value.status_code == 401

    def test_login_creates_token(self, db_session, admin_user):
        result = login(LoginRequest(username="testadmin", password="secureadmin"), db_session)
        token = result["token"]
        assert token in _active_tokens
        assert _active_tokens[token]["username"] == "testadmin"

    def test_login_updates_last_login(self, db_session, admin_user):
        before = admin_user.last_login
        login(LoginRequest(username="testadmin", password="secureadmin"), db_session)
        db_session.refresh(admin_user)
        assert admin_user.last_login is not None
        assert admin_user.last_login != before

    def test_login_creates_audit_log(self, db_session, admin_user):
        login(LoginRequest(username="testadmin", password="secureadmin"), db_session)
        logs = db_session.query(Log).filter(Log.action == "user_login").all()
        assert len(logs) >= 1


# ── Logout ────────────────────────────────────────────────────────────

class TestLogout:
    def test_logout_invalidates_token(self, db_session, admin_user):
        result = login(LoginRequest(username="testadmin", password="secureadmin"), db_session)
        token = result["token"]
        assert token in _active_tokens
        logout(f"Bearer {token}")
        assert token not in _active_tokens

    def test_logout_without_token(self):
        result = logout(None)
        assert result["message"] == "Logged out"


# ── Registration ──────────────────────────────────────────────────────

class TestRegistration:
    def test_register_user_success(self, db_session, admin_user):
        admin_ctx = {"user_id": admin_user.user_id, "username": "testadmin", "role": "admin"}
        result = register_user(
            RegisterRequest(username="newuser", password="newpass", role="user", display_name="New"),
            db_session, admin_ctx,
        )
        assert result["username"] == "newuser"
        assert result["role"] == "user"

    def test_register_duplicate_username(self, db_session, admin_user):
        from fastapi import HTTPException
        admin_ctx = {"user_id": admin_user.user_id, "username": "testadmin", "role": "admin"}
        with pytest.raises(HTTPException) as exc:
            register_user(
                RegisterRequest(username="testadmin", password="pass"),
                db_session, admin_ctx,
            )
        assert exc.value.status_code == 400

    def test_register_creates_audit_log(self, db_session, admin_user):
        admin_ctx = {"user_id": admin_user.user_id, "username": "testadmin", "role": "admin"}
        register_user(
            RegisterRequest(username="logtest", password="pass"),
            db_session, admin_ctx,
        )
        logs = db_session.query(Log).filter(Log.action.like("user_created%")).all()
        assert len(logs) >= 1


# ── Password Change ──────────────────────────────────────────────────

class TestPasswordChange:
    def test_change_password_success(self, db_session, regular_user):
        user_ctx = {"user_id": regular_user.user_id, "username": "testuser", "role": "user"}
        result = change_password(
            PasswordChangeRequest(old_password="userpass123", new_password="newpass456"),
            db_session, user_ctx,
        )
        assert "success" in result["message"].lower()
        # Verify new password works
        assert _verify_password("newpass456", regular_user.password_hash)

    def test_change_password_wrong_old(self, db_session, regular_user):
        from fastapi import HTTPException
        user_ctx = {"user_id": regular_user.user_id, "username": "testuser", "role": "user"}
        with pytest.raises(HTTPException) as exc:
            change_password(
                PasswordChangeRequest(old_password="wrongold", new_password="new"),
                db_session, user_ctx,
            )
        assert exc.value.status_code == 401

    def test_change_password_clears_must_change_flag(self, db_session):
        pw_hash, _ = _hash_password("temp")
        user = User(
            username="forcepw", password_hash=pw_hash, role="user",
            created_at=datetime.now(), is_active=True, must_change_password=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        user_ctx = {"user_id": user.user_id, "username": "forcepw", "role": "user"}
        change_password(
            PasswordChangeRequest(old_password="temp", new_password="newpw"),
            db_session, user_ctx,
        )
        db_session.refresh(user)
        assert user.must_change_password is False


# ── User Management ──────────────────────────────────────────────────

class TestUserManagement:
    def test_list_users(self, db_session, admin_user, regular_user):
        users = list_users(db_session)
        assert len(users) >= 2
        usernames = [u["username"] for u in users]
        assert "testadmin" in usernames
        assert "testuser" in usernames

    def test_delete_user_soft(self, db_session, admin_user, regular_user):
        admin_ctx = {"user_id": admin_user.user_id, "username": "testadmin", "role": "admin"}
        result = delete_user(regular_user.user_id, db_session, admin_ctx)
        assert "deactivated" in result["message"].lower()
        db_session.refresh(regular_user)
        assert regular_user.is_active is False

    def test_cannot_delete_self(self, db_session, admin_user):
        from fastapi import HTTPException
        admin_ctx = {"user_id": admin_user.user_id, "username": "testadmin", "role": "admin"}
        with pytest.raises(HTTPException) as exc:
            delete_user(admin_user.user_id, db_session, admin_ctx)
        assert exc.value.status_code == 400

    def test_delete_invalidates_tokens(self, db_session, admin_user, regular_user):
        # Login regular user first
        result = login(LoginRequest(username="testuser", password="userpass123"), db_session)
        token = result["token"]
        assert token in _active_tokens
        # Admin deletes them
        admin_ctx = {"user_id": admin_user.user_id, "username": "testadmin", "role": "admin"}
        delete_user(regular_user.user_id, db_session, admin_ctx)
        assert token not in _active_tokens


# ── Default Admin Initialization ──────────────────────────────────────

class TestDefaultAdmin:
    def test_creates_admin_when_empty(self, db_session):
        init_default_admin(db_session)
        admin = db_session.query(User).filter(User.username == "admin").first()
        assert admin is not None
        assert admin.role == "admin"
        assert admin.must_change_password is True

    def test_default_admin_can_login(self, db_session):
        init_default_admin(db_session)
        result = login(LoginRequest(username="admin", password="admin123"), db_session)
        assert result["user"]["username"] == "admin"

    def test_does_not_duplicate_admin(self, db_session, admin_user):
        """If users exist, don't create another admin."""
        init_default_admin(db_session)
        admins = db_session.query(User).filter(User.username == "admin").all()
        assert len(admins) == 0  # didn't create because users already exist


# ── Permissions ───────────────────────────────────────────────────────

class TestPermissions:
    def test_admin_has_all_permissions(self):
        perms = get_permissions("admin")
        assert all(perms.values())

    def test_user_cannot_approve_drafts(self):
        assert has_permission("user", "can_approve_drafts") is False

    def test_user_cannot_manage_users(self):
        assert has_permission("user", "can_manage_users") is False

    def test_user_cannot_delete_clients(self):
        assert has_permission("user", "can_delete_clients") is False

    def test_user_can_chat(self):
        assert has_permission("user", "can_chat") is True

    def test_user_can_upload(self):
        assert has_permission("user", "can_upload") is True

    def test_user_can_view_analytics(self):
        assert has_permission("user", "can_view_analytics") is True

    def test_user_cannot_view_logs(self):
        assert has_permission("user", "can_view_logs") is False

    def test_check_permission_with_none_user(self):
        assert check_permission(None, "can_chat") is False

    def test_admin_roles_match_definition(self):
        admin_perms = ROLES["admin"]
        assert len(admin_perms) == 11  # all permission keys
        for k, v in admin_perms.items():
            assert v is True

    def test_unknown_role_falls_back_to_user(self):
        perms = get_permissions("unknown_role")
        assert perms == ROLES["user"]
