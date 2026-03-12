"""
Autify Engine V1 — Unit Tests: LLM Output Schema Validation
Ensures all LLM-generated drafts conform to expected schemas
and are always marked as DRAFT (approved=False).
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from llm.orchestrator import LocalLLMOrchestrator, process_results_into_draft


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def orchestrator():
    return LocalLLMOrchestrator()


@pytest.fixture
def sample_analysis():
    return {
        "kpi_summary": {"revenue_sum": 50000, "revenue_mean": 12500},
        "anomalies": [{"column": "discount", "value": 95, "reason": "Z-score > 3"}],
    }


# ── Draft-only enforcement ───────────────────────────────────────────

class TestDraftOnlyEnforcement:
    def test_email_draft_never_approved(self, sample_analysis):
        result = process_results_into_draft(sample_analysis, "email", None)
        assert result["approved"] is False

    def test_calendar_draft_never_approved(self, sample_analysis):
        result = process_results_into_draft(sample_analysis, "calendar", None)
        assert result["approved"] is False

    def test_report_draft_never_approved(self, sample_analysis):
        result = process_results_into_draft(sample_analysis, "report", None)
        assert result["approved"] is False

    def test_unknown_type_never_approved(self, sample_analysis):
        result = process_results_into_draft(sample_analysis, "unknown_type", None)
        assert result["approved"] is False


# ── Schema validation ────────────────────────────────────────────────

class TestDraftSchemaValidation:
    def test_email_has_subject_and_body(self, orchestrator):
        draft = orchestrator.generate_draft({}, {}, "email")
        assert "subject" in draft
        assert "body" in draft
        assert "[DRAFT]" in draft["subject"] or "[DRAFT" in draft["body"]

    def test_calendar_has_title(self, orchestrator):
        draft = orchestrator.generate_draft({}, {}, "calendar")
        assert "title" in draft
        assert "start_time" in draft

    def test_report_has_sections(self, orchestrator):
        draft = orchestrator.generate_draft({}, {}, "report")
        assert "title" in draft
        assert "sections" in draft

    def test_content_is_json_serializable(self, sample_analysis):
        result = process_results_into_draft(sample_analysis, "email", None)
        # Must be serializable for storage in JSON column
        serialized = json.dumps(result["content"])
        assert isinstance(serialized, str)
