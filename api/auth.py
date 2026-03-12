"""
Autify Engine V1 - Authentication & User Management
Local-only user auth with hashed passwords (bcrypt via hashlib fallback).
Roles: admin (full access) | user (limited access).
"""

import hashlib
import secrets
import os
from datetime import datetime
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import models, database

# --- Token store (in-memory, per-process) ---
# Maps token -> {"user_id": int, "username": str, "role": str}
_active_tokens: dict[str, dict] = {}

# --- Password hashing (SHA-256 + salt, no external deps) ---
def _hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """Hash password with SHA-256 + random salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}${hashed}", salt


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt$hash."""
    if "$" not in stored_hash:
        return False
    salt, _ = stored_hash.split("$", 1)
    check_hash, _ = _hash_password(password, salt)
    return check_hash == stored_hash


# --- Pydantic schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    display_name: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    role: str
    display_name: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False


# --- Auth helpers ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Extract user from Bearer token. Returns None if no auth."""
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return _active_tokens.get(token)


def require_user(authorization: Optional[str] = Header(None)) -> dict:
    """Require a valid logged-in user."""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_admin(authorization: Optional[str] = Header(None)) -> dict:
    """Require admin role."""
    user = require_user(authorization)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def init_default_admin(db: Session):
    """Create default admin user if no users exist."""
    user_count = db.query(models.User).count()
    if user_count == 0:
        pw_hash, _ = _hash_password("admin123")
        admin = models.User(
            username="admin",
            password_hash=pw_hash,
            role="admin",
            display_name="Administrator",
            created_at=datetime.now(),
            is_active=True,
            must_change_password=True,
        )
        db.add(admin)
        db.commit()
        db.add(models.Log(
            action="default_admin_created",
            timestamp=datetime.now(),
            user_id="System",
        ))
        db.commit()


# --- Auth endpoint functions (called from main.py) ---
def login(payload: LoginRequest, db: Session) -> dict:
    """Authenticate user, return token."""
    user = db.query(models.User).filter(
        models.User.username == payload.username,
        models.User.is_active == True,
    ).first()
    if not user or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_hex(32)
    _active_tokens[token] = {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "display_name": user.display_name or user.username,
    }
    user.last_login = datetime.now()
    db.commit()

    db.add(models.Log(
        action="user_login",
        timestamp=datetime.now(),
        user_id=user.username,
    ))
    db.commit()

    return {
        "token": token,
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "display_name": user.display_name or user.username,
            "must_change_password": user.must_change_password,
        },
    }


def logout(authorization: Optional[str] = None) -> dict:
    """Invalidate token."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        _active_tokens.pop(token, None)
    return {"message": "Logged out"}


def register_user(payload: RegisterRequest, db: Session, admin_user: dict) -> dict:
    """Admin creates a new user."""
    existing = db.query(models.User).filter(models.User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    pw_hash, _ = _hash_password(payload.password)
    new_user = models.User(
        username=payload.username,
        password_hash=pw_hash,
        role=payload.role if payload.role in ("admin", "user") else "user",
        display_name=payload.display_name or payload.username,
        created_at=datetime.now(),
        is_active=True,
        must_change_password=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    db.add(models.Log(
        action=f"user_created:{new_user.username}",
        timestamp=datetime.now(),
        user_id=admin_user["username"],
    ))
    db.commit()

    return {
        "user_id": new_user.user_id,
        "username": new_user.username,
        "role": new_user.role,
        "display_name": new_user.display_name,
    }


def change_password(payload: PasswordChangeRequest, db: Session, current_user: dict) -> dict:
    """User changes own password."""
    user = db.query(models.User).filter(models.User.user_id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not _verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    pw_hash, _ = _hash_password(payload.new_password)
    user.password_hash = pw_hash
    user.must_change_password = False
    db.commit()

    db.add(models.Log(
        action="password_changed",
        timestamp=datetime.now(),
        user_id=current_user["username"],
    ))
    db.commit()

    return {"message": "Password changed successfully"}


def list_users(db: Session) -> list:
    """Admin lists all users."""
    users = db.query(models.User).all()
    return [
        {
            "user_id": u.user_id,
            "username": u.username,
            "role": u.role,
            "display_name": u.display_name,
            "is_active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


def delete_user(user_id: int, db: Session, admin_user: dict) -> dict:
    """Admin deactivates a user (soft delete)."""
    if admin_user["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()

    # Invalidate their tokens
    to_remove = [t for t, u in _active_tokens.items() if u["user_id"] == user_id]
    for t in to_remove:
        del _active_tokens[t]

    db.add(models.Log(
        action=f"user_deactivated:{user.username}",
        timestamp=datetime.now(),
        user_id=admin_user["username"],
    ))
    db.commit()

    return {"message": f"User '{user.username}' deactivated"}
