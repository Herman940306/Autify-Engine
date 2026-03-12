"""
Autify Engine V1 — Central Configuration
All environment settings live here. Zero-Cloud principle:
no external URLs except the optional license server.
"""

import os

# ── Ports (high-numbered, configurable) ───────────────────────────────
BACKEND_PORT   = int(os.getenv("BACKEND_PORT", "18080"))
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "18300"))
LLM_PORT       = int(os.getenv("LLM_PORT", "11434"))

# ── Database ──────────────────────────────────────────────────────────
DB_PATH      = os.getenv("DB_PATH", "data/db.sqlite")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///./{DB_PATH}")

# ── Local LLM ────────────────────────────────────────────────────────
LLM_HOST    = os.getenv("LLM_HOST", "localhost")
LLM_API_URL = os.getenv("LLM_API_URL", f"http://{LLM_HOST}:{LLM_PORT}")
LLM_MODEL   = os.getenv("LLM_MODEL", "llama3.2:3b")

# ── License ──────────────────────────────────────────────────────────
LICENSE_SERVER_URL = os.getenv("LICENSE_SERVER_URL", "http://localhost:9090")
LICENSE_FILE_PATH  = os.getenv("LICENSE_FILE_PATH", "license.json")

# ── Telemetry (opt-in only) ──────────────────────────────────────────
TELEMETRY_ENABLED = os.getenv("TELEMETRY_ENABLED", "false").lower() == "true"

# ── Application ──────────────────────────────────────────────────────
APP_NAME    = "Autify Engine V1"
APP_VERSION = "1.0.0"
DRAFT_ONLY  = True  # Cannot be overridden — architectural constraint

# ── 10 LLM Laws ──────────────────────────────────────────────────────
LLM_LAWS = [
    "1. All outputs are DRAFTS — never auto-executed.",
    "2. Human approval required before any action.",
    "3. No data leaves the local machine (Zero-Cloud).",
    "4. All inputs are validated and sanitized.",
    "5. Deterministic analysis — no randomness in KPIs.",
    "6. Append-only audit logs — immutable history.",
    "7. Hardware-bound licensing — one device per key.",
    "8. No PII in LLM prompts — template variables only.",
    "9. True Data Only -- all chat responses from local LLM; failures return errors, never templates.",
    "10. All drafts carry draft_flag=True until human approval.",
]
