"""
Autify Engine V1 - Chat Bot Backend
Sends queries to local LLM service only (Zero-Cloud).All responses are TRUE DATA from local LLM only -- no template fallback.
Schema validation ensures structured outputs comply with expected formats.All responses are read-only / draft-only per LLM Laws.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import get_chat_system_prompt

logger = logging.getLogger("autify.chat")

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    from core.config import LLM_API_URL, LLM_MODEL
except ImportError:
    LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    source: str  # "llm" or "error" (never "fallback")
    draft_warning: bool
    session_id: Optional[str] = None


# Keywords that trigger draft-only warnings
_ACTION_KEYWORDS = [
    "send", "email", "schedule", "create", "delete", "update", "modify",
    "execute", "run", "approve", "submit", "post", "publish", "invoice",
    "calendar", "meeting", "notify", "alert", "change", "edit", "remove",
]


def _detect_action_intent(message: str) -> bool:
    """Check if user message implies wanting to perform an action."""
    lower = message.lower()
    return any(kw in lower for kw in _ACTION_KEYWORDS)


def _build_draft_warning(message: str) -> str:
    """Build a draft-only safety warning for action requests."""
    return (
        "\n\n---\n"
        "**Draft-Only Notice:** This suggestion is informational only. "
        "To execute any action, please create a Draft via the Drafts page "
        "and have it approved by an authorized user. "
        "Autify Engine never executes actions automatically (LLM Law #1 & #2)."
    )


# ── LLM unavailable error message ─────────────────────────────────────
_LLM_UNAVAILABLE_MSG = (
    "LLM temporarily unavailable or cannot generate a valid response. "
    "Please try again."
)

# ── Response schema definitions (validation only -- never used as user output) ──
_RESPONSE_SCHEMAS = {
    "email": {
        "required_fields": ["subject", "body", "to"],
        "field_types": {"subject": str, "body": str, "to": str, "cc": str},
    },
    "kpi_report": {
        "required_fields": ["title", "metrics"],
        "field_types": {"title": str, "metrics": list, "period": str},
    },
    "draft_output": {
        "required_fields": ["content", "draft_flag"],
        "field_types": {"content": str, "draft_flag": bool, "category": str},
    },
    "calendar_event": {
        "required_fields": ["title", "date"],
        "field_types": {"title": str, "date": str, "description": str},
    },
    "invoice": {
        "required_fields": ["client", "items", "total"],
        "field_types": {"client": str, "items": list, "total": (int, float)},
    },
}


def _detect_structured_intent(message: str) -> Optional[str]:
    """Detect if the message expects a structured (JSON) response type."""
    lower = message.lower()
    if any(w in lower for w in ["email", "mail", "compose"]):
        return "email"
    if any(w in lower for w in ["kpi", "metric"]):
        return "kpi_report"
    if any(w in lower for w in ["invoice", "bill"]):
        return "invoice"
    if any(w in lower for w in ["calendar", "event", "meeting", "schedule"]):
        return "calendar_event"
    if any(w in lower for w in ["draft output", "generate draft"]):
        return "draft_output"
    return None


def _validate_response_schema(response_text: str, schema_type: str) -> tuple:
    """
    Validate LLM response against the expected schema.
    Used ONLY for structured outputs (emails, KPIs, drafts).
    Templates define required fields / types -- never populate missing data.
    Returns (is_valid: bool, error_message: str).
    """
    if schema_type not in _RESPONSE_SCHEMAS:
        return True, ""  # No schema for this type -- plain text is accepted

    schema = _RESPONSE_SCHEMAS[schema_type]

    # Attempt to extract JSON from the response
    try:
        data = json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        # Try to find JSON block inside markdown fences
        import re
        match = re.search(r"```(?:json)?\s*({.*?})\s*```", response_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
            except (json.JSONDecodeError, TypeError):
                return False, f"LLM response is not valid JSON for {schema_type} output."
        else:
            return False, f"LLM response is not valid JSON for {schema_type} output."

    # Check required fields
    for field in schema["required_fields"]:
        if field not in data:
            return False, f"LLM response missing required field: {field}"

    # Check field types
    for field, expected_type in schema["field_types"].items():
        if field in data and not isinstance(data[field], expected_type):
            type_name = expected_type.__name__ if hasattr(expected_type, '__name__') else str(expected_type)
            return False, f"Field '{field}' has wrong type (expected {type_name})"

    return True, ""


def _call_local_llm(system_prompt: str, user_message: str, history: list = None) -> Optional[str]:
    """Call the local LLM server (Ollama-compatible API). Zero-Cloud only."""
    if not _HAS_REQUESTS:
        return None

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-10:])  # Last 10 messages for context
    messages.append({"role": "user", "content": user_message})

    try:
        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "num_thread": 4,
                "num_predict": 512,
            },
        }
        r = requests.post(
            f"{LLM_API_URL}/api/chat",
            json=payload,
            timeout=120,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("message", {}).get("content", "")
    except Exception as exc:
        logger.debug("Chat LLM call failed: %s", exc)
    return None


def process_chat_message(
    message: str,
    user: dict,
    db: Session,
    session_id: str = None,
) -> dict:
    """
    Process a chat message through the local LLM ONLY.

    TRUE DATA policy:
    - All user-facing responses come exclusively from the local LLM.
    - If the LLM is unavailable or returns an invalid response, the user
      receives a clear error message -- NEVER template/mock/placeholder data.
    - Templates are used ONLY for schema validation of structured outputs.

    Enforces:
    - Zero-Cloud (local LLM only)
    - Draft-only (action intents get warnings)
    - All 10 LLM Laws via system prompt
    """
    from database.models import ChatMessage

    is_action = _detect_action_intent(message)
    system_prompt = get_chat_system_prompt()

    # Save user message
    db.add(ChatMessage(
        user_id=user.get("username", "anonymous"),
        role="user",
        content=message,
        timestamp=datetime.now(),
        session_id=session_id,
    ))
    db.commit()

    # Call local LLM -- the ONLY source of user-facing content
    llm_response = _call_local_llm(system_prompt, message)

    if llm_response:
        # Schema validation for structured output intents
        structured_type = _detect_structured_intent(message)
        if structured_type:
            is_valid, err = _validate_response_schema(llm_response, structured_type)
            if not is_valid:
                reply = (
                    "LLM response did not match the expected schema. "
                    f"{err} Please try rephrasing your request."
                )
                source = "error"
            else:
                reply = llm_response
                source = "llm"
        else:
            reply = llm_response
            source = "llm"
    else:
        # LLM unavailable -- return error, NEVER template/mock content
        reply = _LLM_UNAVAILABLE_MSG
        source = "error"

    # Append draft warning if action intent detected
    if is_action:
        reply += _build_draft_warning(message)

    # Save assistant response
    db.add(ChatMessage(
        user_id="assistant",
        role="assistant",
        content=reply,
        timestamp=datetime.now(),
        session_id=session_id,
    ))
    db.commit()

    return {
        "reply": reply,
        "source": source,
        "draft_warning": is_action,
        "session_id": session_id,
    }


def get_chat_history(user: dict, db: Session, session_id: str = None, limit: int = 50) -> list:
    """Retrieve chat history for a user."""
    from database.models import ChatMessage

    query = db.query(ChatMessage).filter(
        ChatMessage.user_id.in_([user.get("username", "anonymous"), "assistant"])
    )
    if session_id:
        query = query.filter(ChatMessage.session_id == session_id)

    messages = query.order_by(ChatMessage.timestamp.desc()).limit(limit).all()
    messages.reverse()

    return [
        {
            "message_id": m.message_id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "session_id": m.session_id,
        }
        for m in messages
    ]


def export_chat_history(user: dict, db: Session) -> str:
    """Export chat history as JSON string."""
    history = get_chat_history(user, db, limit=500)
    return json.dumps(history, indent=2)
