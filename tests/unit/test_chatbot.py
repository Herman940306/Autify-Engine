"""
Autify Engine V1 -- QA Tests: Chat Bot
Tests TRUE DATA enforcement (LLM-only responses),
schema validation, draft-only warnings, action detection,
and chat history.  No template fallback is ever returned.
"""

import os
import sys
import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, ChatMessage
from api.chat import (
    _detect_action_intent,
    _detect_structured_intent,
    _validate_response_schema,
    _LLM_UNAVAILABLE_MSG,
    _RESPONSE_SCHEMAS,
    process_chat_message,
    get_chat_history,
    ChatRequest,
)
from core.security import get_chat_system_prompt, CHAT_SAFETY_RULES


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def db_session(tmp_path):
    """Fresh DB per test."""
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def user_context():
    """Standard user context dict."""
    return {
        "user_id": 1,
        "username": "testuser",
        "role": "user",
        "display_name": "Test User",
    }


# ── Action Intent Detection ──────────────────────────────────────────

class TestActionDetection:
    def test_detects_send_email(self):
        assert _detect_action_intent("send an email to the client") is True

    def test_detects_approve(self):
        assert _detect_action_intent("approve the draft now") is True

    def test_detects_execute(self):
        assert _detect_action_intent("execute this action immediately") is True

    def test_detects_submit(self):
        assert _detect_action_intent("submit the report to management") is True

    def test_detects_publish(self):
        assert _detect_action_intent("publish the analysis results") is True

    def test_no_action_on_question(self):
        assert _detect_action_intent("what is the total revenue?") is False

    def test_no_action_on_help(self):
        assert _detect_action_intent("how do I use Autify Engine?") is False

    def test_no_action_on_greeting(self):
        assert _detect_action_intent("hello") is False


# ── TRUE DATA Enforcement (No Template Fallback) ─────────────────────

class TestTrueDataEnforcement:
    """Verify that NO template/mock/placeholder content is ever returned."""

    def test_llm_failure_returns_error_not_template(self, db_session, user_context):
        """When LLM is offline, response must be an error message, not template."""
        result = process_chat_message(
            "help me with the system", user_context, db_session, "td1",
        )
        assert result["source"] == "error"
        assert result["reply"] == _LLM_UNAVAILABLE_MSG

    def test_no_template_content_on_upload_question(self, db_session, user_context):
        """Upload question must NOT get a canned template response."""
        result = process_chat_message(
            "how do I upload a file?", user_context, db_session, "td2",
        )
        assert result["source"] == "error"
        # Must NOT contain template-style content
        assert "Go to the **Inputs** page" not in result["reply"]
        assert _LLM_UNAVAILABLE_MSG in result["reply"]

    def test_no_template_content_on_draft_question(self, db_session, user_context):
        """Draft question must NOT get a canned template response."""
        result = process_chat_message(
            "tell me about drafts", user_context, db_session, "td3",
        )
        assert result["source"] == "error"
        assert "Draft Workflow" not in result["reply"]

    def test_no_template_content_on_greeting(self, db_session, user_context):
        """Greeting must NOT get a canned template response."""
        result = process_chat_message(
            "hello there!", user_context, db_session, "td4",
        )
        assert result["source"] == "error"
        assert "I'm Autify Assistant" not in result["reply"]

    def test_no_template_content_on_unknown(self, db_session, user_context):
        """Unknown topic must NOT get a canned fallback."""
        result = process_chat_message(
            "xyzzy plugh 12345", user_context, db_session, "td5",
        )
        assert result["source"] == "error"
        assert "LLM service is currently offline" not in result["reply"]
        assert _LLM_UNAVAILABLE_MSG in result["reply"]

    def test_source_is_never_fallback(self, db_session, user_context):
        """The source field must never be 'fallback'."""
        for msg in ["help", "upload a csv", "hello", "what is analysis?"]:
            result = process_chat_message(
                msg, user_context, db_session, f"nf_{msg[:4]}",
            )
            assert result["source"] != "fallback", f"Got 'fallback' for: {msg}"

    @patch("api.chat._call_local_llm")
    def test_llm_success_returns_llm_source(self, mock_llm, db_session, user_context):
        """When LLM responds successfully, source must be 'llm'."""
        mock_llm.return_value = "Here is the real LLM answer."
        result = process_chat_message(
            "what is revenue?", user_context, db_session, "td6",
        )
        assert result["source"] == "llm"
        assert result["reply"] == "Here is the real LLM answer."

    @patch("api.chat._call_local_llm")
    def test_llm_empty_string_treated_as_failure(self, mock_llm, db_session, user_context):
        """Empty LLM response should be treated as failure."""
        mock_llm.return_value = ""
        result = process_chat_message(
            "hello", user_context, db_session, "td7",
        )
        # Empty string is falsy, should trigger error path
        assert result["source"] == "error"
        assert _LLM_UNAVAILABLE_MSG in result["reply"]

    @patch("api.chat._call_local_llm")
    def test_llm_none_treated_as_failure(self, mock_llm, db_session, user_context):
        """None LLM response should trigger error."""
        mock_llm.return_value = None
        result = process_chat_message(
            "hello", user_context, db_session, "td8",
        )
        assert result["source"] == "error"


# ── Schema Validation ────────────────────────────────────────────────

class TestSchemaValidation:
    """Verify structured output schema validation."""

    def test_valid_email_schema(self):
        email_json = json.dumps({"subject": "Test", "body": "Hello", "to": "user@example.com"})
        valid, err = _validate_response_schema(email_json, "email")
        assert valid is True
        assert err == ""

    def test_email_missing_subject_fails(self):
        email_json = json.dumps({"body": "Hello", "to": "user@example.com"})
        valid, err = _validate_response_schema(email_json, "email")
        assert valid is False
        assert "subject" in err

    def test_email_missing_body_fails(self):
        email_json = json.dumps({"subject": "Test", "to": "user@example.com"})
        valid, err = _validate_response_schema(email_json, "email")
        assert valid is False
        assert "body" in err

    def test_valid_kpi_report_schema(self):
        kpi_json = json.dumps({"title": "Q1 Report", "metrics": [1, 2, 3]})
        valid, err = _validate_response_schema(kpi_json, "kpi_report")
        assert valid is True

    def test_kpi_missing_metrics_fails(self):
        kpi_json = json.dumps({"title": "Q1 Report"})
        valid, err = _validate_response_schema(kpi_json, "kpi_report")
        assert valid is False
        assert "metrics" in err

    def test_valid_invoice_schema(self):
        inv_json = json.dumps({"client": "Acme", "items": ["Widget"], "total": 99.50})
        valid, err = _validate_response_schema(inv_json, "invoice")
        assert valid is True

    def test_invoice_wrong_type_fails(self):
        inv_json = json.dumps({"client": "Acme", "items": "not-a-list", "total": 100})
        valid, err = _validate_response_schema(inv_json, "invoice")
        assert valid is False
        assert "items" in err

    def test_valid_calendar_event_schema(self):
        ev_json = json.dumps({"title": "Standup", "date": "2026-03-02"})
        valid, err = _validate_response_schema(ev_json, "calendar_event")
        assert valid is True

    def test_calendar_missing_date_fails(self):
        ev_json = json.dumps({"title": "Standup"})
        valid, err = _validate_response_schema(ev_json, "calendar_event")
        assert valid is False
        assert "date" in err

    def test_valid_draft_output_schema(self):
        draft_json = json.dumps({"content": "Report text", "draft_flag": True})
        valid, err = _validate_response_schema(draft_json, "draft_output")
        assert valid is True

    def test_draft_output_missing_draft_flag_fails(self):
        draft_json = json.dumps({"content": "Report text"})
        valid, err = _validate_response_schema(draft_json, "draft_output")
        assert valid is False
        assert "draft_flag" in err

    def test_non_json_response_fails(self):
        valid, err = _validate_response_schema("This is plain text", "email")
        assert valid is False
        assert "not valid JSON" in err

    def test_json_in_markdown_fence_accepted(self):
        md = '```json\n{"subject": "Hi", "body": "World", "to": "a@b.com"}\n```'
        valid, err = _validate_response_schema(md, "email")
        assert valid is True

    def test_unknown_schema_passes(self):
        """Unknown schema type should pass (no validation needed for plain chat)."""
        valid, err = _validate_response_schema("hello world", "unknown_type")
        assert valid is True

    def test_schemas_exist_for_key_types(self):
        """Ensure schemas are defined for all critical structured types."""
        for key in ["email", "kpi_report", "draft_output", "calendar_event", "invoice"]:
            assert key in _RESPONSE_SCHEMAS

    @patch("api.chat._call_local_llm")
    def test_invalid_schema_rejects_llm_response(self, mock_llm, db_session, user_context):
        """LLM returns bad JSON for email -- must be rejected, not auto-filled."""
        mock_llm.return_value = json.dumps({"body": "Hello"})  # missing subject, to
        result = process_chat_message(
            "compose an email to john", user_context, db_session, "sv1",
        )
        assert result["source"] == "error"
        assert "missing required field" in result["reply"].lower()

    @patch("api.chat._call_local_llm")
    def test_valid_schema_accepted(self, mock_llm, db_session, user_context):
        """LLM returns valid email JSON -- must be accepted as-is."""
        good_email = json.dumps({"subject": "Hi", "body": "Hello", "to": "john@co.com"})
        mock_llm.return_value = good_email
        result = process_chat_message(
            "compose an email to john", user_context, db_session, "sv2",
        )
        assert result["source"] == "llm"
        # Reply starts with the valid JSON (draft warning may be appended for action intent)
        assert result["reply"].startswith(good_email)


# ── Structured Intent Detection ──────────────────────────────────────

class TestStructuredIntentDetection:
    def test_email_intent(self):
        assert _detect_structured_intent("compose an email to John") == "email"

    def test_kpi_intent(self):
        assert _detect_structured_intent("show me the kpi dashboard") == "kpi_report"

    def test_invoice_intent(self):
        assert _detect_structured_intent("generate an invoice for Acme") == "invoice"

    def test_calendar_intent(self):
        assert _detect_structured_intent("schedule a meeting tomorrow") == "calendar_event"

    def test_draft_output_intent(self):
        assert _detect_structured_intent("generate draft output for review") == "draft_output"

    def test_plain_question_no_intent(self):
        assert _detect_structured_intent("what is the total revenue?") is None

    def test_greeting_no_intent(self):
        assert _detect_structured_intent("hello") is None


# ── Draft-Only Enforcement in Chat ────────────────────────────────────

class TestChatDraftOnly:
    def test_action_message_gets_draft_warning(self, db_session, user_context):
        result = process_chat_message(
            "send this email now", user_context, db_session, "test1",
        )
        assert result["draft_warning"] is True

    def test_question_no_draft_warning(self, db_session, user_context):
        result = process_chat_message(
            "what is installed?", user_context, db_session, "test2",
        )
        assert result["draft_warning"] is False

    def test_response_always_has_content(self, db_session, user_context):
        result = process_chat_message(
            "hello", user_context, db_session, "test3",
        )
        assert "reply" in result
        assert len(result["reply"]) > 0

    @patch("api.chat._call_local_llm")
    def test_draft_only_cannot_be_bypassed(self, mock_llm, db_session, user_context):
        """Even when LLM responds, action intents still get draft warnings."""
        mock_llm.return_value = "Sure, I'll send that email right away!"
        result = process_chat_message(
            "send an email to the client", user_context, db_session, "bypass1",
        )
        assert result["draft_warning"] is True
        assert "Draft-Only Notice" in result["reply"]

    @patch("api.chat._call_local_llm")
    def test_draft_warning_on_schedule(self, mock_llm, db_session, user_context):
        """Schedule action must include draft warning."""
        mock_llm.return_value = "Meeting scheduled for tomorrow."
        result = process_chat_message(
            "schedule a meeting for tomorrow", user_context, db_session, "bypass2",
        )
        assert result["draft_warning"] is True
        assert "Draft-Only Notice" in result["reply"]


# ── Chat History ──────────────────────────────────────────────────────

class TestChatHistory:
    def test_messages_saved_to_db(self, db_session, user_context):
        process_chat_message(
            "test message", user_context, db_session, "hist1",
        )
        messages = db_session.query(ChatMessage).filter(
            ChatMessage.session_id == "hist1"
        ).all()
        # Should have both user message and assistant response
        assert len(messages) == 2
        roles = {m.role for m in messages}
        assert "user" in roles
        assert "assistant" in roles

    def test_get_chat_history(self, db_session, user_context):
        process_chat_message(
            "first msg", user_context, db_session, "hist2",
        )
        process_chat_message(
            "second msg", user_context, db_session, "hist2",
        )
        history = get_chat_history(user_context, db_session, session_id="hist2")
        assert len(history) == 4  # 2 user + 2 assistant

    def test_history_has_required_fields(self, db_session, user_context):
        process_chat_message(
            "fields test", user_context, db_session, "hist3",
        )
        history = get_chat_history(user_context, db_session, session_id="hist3")
        for msg in history:
            assert "role" in msg
            assert "content" in msg
            assert "timestamp" in msg

    def test_history_isolated_by_session(self, db_session, user_context):
        process_chat_message(
            "session A", user_context, db_session, "sessA",
        )
        process_chat_message(
            "session B", user_context, db_session, "sessB",
        )
        histA = get_chat_history(user_context, db_session, session_id="sessA")
        histB = get_chat_history(user_context, db_session, session_id="sessB")
        a_contents = [m["content"] for m in histA]
        b_contents = [m["content"] for m in histB]
        assert "session A" in a_contents
        assert "session B" not in a_contents
        assert "session B" in b_contents


# ── Chat Safety / LLM Laws ───────────────────────────────────────────

class TestChatSafety:
    def test_safety_rules_exist(self):
        assert len(CHAT_SAFETY_RULES) > 0

    def test_system_prompt_includes_draft_only(self):
        prompt = get_chat_system_prompt()
        assert "draft" in prompt.lower()

    def test_system_prompt_includes_zero_cloud(self):
        prompt = get_chat_system_prompt()
        assert "local" in prompt.lower() or "zero" in prompt.lower()

    def test_system_prompt_includes_human_approval(self):
        prompt = get_chat_system_prompt()
        assert "human" in prompt.lower() or "approval" in prompt.lower()

    def test_system_prompt_is_string(self):
        prompt = get_chat_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50
