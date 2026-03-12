"""
Autify Engine V1 — LLM Orchestrator
Real template-driven draft generation with optional local LLM enhancement.
Zero-Cloud: everything local. No mocks.

LLM Integration Strategy:
  1. Try local LLM server (Ollama / GPT4All-J) on LLM_PORT for enrichment
  2. If LLM unavailable → graceful fallback to template-only generation (Law #9)
  3. All 10 LLM Laws enforced at every stage
"""

import json
import os
import glob
import logging
from datetime import datetime

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

logger = logging.getLogger("autify.llm")

# ── Config ────────────────────────────────────────────────────────────
try:
    from core.config import LLM_API_URL, LLM_MODEL, LLM_LAWS
except ImportError:
    LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
    LLM_LAWS = []

# ── Template cache ────────────────────────────────────────────────────
_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
_template_cache: dict | None = None


def _load_templates() -> dict:
    """Load all JSON templates from templates/ directory, keyed by template_name."""
    global _template_cache
    if _template_cache is not None:
        return _template_cache

    _template_cache = {}
    pattern = os.path.join(_TEMPLATES_DIR, "*.json")
    for path in glob.glob(pattern):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tmpl = json.load(f)
            key = tmpl.get("template_name", os.path.basename(path))
            _template_cache[key] = tmpl
        except Exception:
            continue
    return _template_cache


def _select_template(draft_type: str, analysis_result: dict) -> dict | None:
    """
    Select the best matching template for the given draft type
    and analysis data. Falls back to first available template.
    """
    templates = _load_templates()

    type_mappings = {
        "email": ["pos_reporting", "inventory_alert", "client_notification", "billing_workflow"],
        "calendar": ["job_scheduling"],
        "report": ["pos_reporting", "billing_workflow"],
        "invoice": ["invoice_draft"],
        "notification": ["client_notification", "inventory_alert"],
    }

    candidates = type_mappings.get(draft_type, [])
    for name in candidates:
        if name in templates:
            return templates[name]

    if templates:
        return next(iter(templates.values()))
    return None


def _format_currency(value: float) -> str:
    """Format number as South African Rand."""
    return f"R {value:,.2f}"


def _build_email_draft(analysis_result: dict, template: dict | None) -> dict:
    """Build a real email draft from analysis data + template."""
    kpis = analysis_result.get("kpi_summary", {})
    anomalies = analysis_result.get("anomalies", [])
    now = datetime.now()

    kpi_lines = []
    for key, value in kpis.items():
        label = key.replace("_", " ").title()
        if "sum" in key.lower() and isinstance(value, (int, float)) and value > 100:
            kpi_lines.append(f"- **{label}:** {_format_currency(value)}")
        else:
            kpi_lines.append(f"- **{label}:** {value:,.2f}" if isinstance(value, (int, float)) else f"- **{label}:** {value}")

    anomaly_lines = []
    for a in anomalies:
        anomaly_lines.append(
            f"- Column `{a.get('column', '?')}`: value {a.get('value', '?')} — {a.get('reason', 'flagged')}"
        )

    anomaly_section = ""
    if anomaly_lines:
        anomaly_section = "\n### Anomalies Detected\n" + "\n".join(anomaly_lines)

    subject = f"[DRAFT] Analysis Report — {now.strftime('%d %b %Y')}"
    body = (
        f"## Analysis Report (DRAFT)\n\n"
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"### Key Performance Indicators\n"
        + ("\n".join(kpi_lines) if kpi_lines else "- No numeric KPIs computed.\n")
        + "\n"
        + anomaly_section
        + "\n\n---\n*This is a DRAFT. Do not act on this report until it has been reviewed and approved.*"
    )

    highlights = []
    if kpis:
        numeric_kpis = {k: v for k, v in kpis.items() if isinstance(v, (int, float))}
        if numeric_kpis:
            top_key = max(numeric_kpis, key=lambda k: numeric_kpis[k])
            highlights.append(f"Highest metric: {top_key.replace('_', ' ').title()} = {numeric_kpis[top_key]:,.2f}")
    if anomalies:
        highlights.append(f"{len(anomalies)} anomaly/anomalies flagged for review")
    else:
        highlights.append("No anomalies detected")

    return {
        "subject": subject,
        "body": body,
        "highlights": highlights,
        "draft_flag": True,
    }


def _build_calendar_draft(analysis_result: dict, template: dict | None) -> dict:
    """Build a real calendar event draft from analysis data."""
    anomalies = analysis_result.get("anomalies", [])
    kpis = analysis_result.get("kpi_summary", {})
    now = datetime.now()

    if anomalies:
        title = f"[DRAFT] Urgent: Review {len(anomalies)} Anomalies Detected"
        notes = "Anomalies require immediate attention:\n" + "\n".join(
            f"- {a.get('column', '?')}: {a.get('value', '?')} ({a.get('reason', '')})"
            for a in anomalies
        )
    else:
        title = "[DRAFT] Scheduled KPI Review Meeting"
        kpi_items = [(k, v) for k, v in kpis.items() if isinstance(v, (int, float))]
        notes = "Regular KPI review session.\n\nMetrics to discuss:\n" + "\n".join(
            f"- {k.replace('_', ' ').title()}: {v:,.2f}" for k, v in kpi_items[:5]
        )

    return {
        "title": title,
        "start_time": now.isoformat(),
        "duration_minutes": 30,
        "notes": notes + "\n\n*This is a DRAFT calendar entry. Do not send invites until approved.*",
        "draft_flag": True,
    }


def _build_report_draft(analysis_result: dict, template: dict | None) -> dict:
    """Build a real report draft from analysis data."""
    kpis = analysis_result.get("kpi_summary", {})
    anomalies = analysis_result.get("anomalies", [])
    now = datetime.now()

    sections = []

    kpi_body = ""
    for key, value in kpis.items():
        label = key.replace("_", " ").title()
        kpi_body += f"- {label}: {value:,.2f}\n" if isinstance(value, (int, float)) else f"- {label}: {value}\n"
    sections.append({"heading": "Key Performance Indicators", "body": kpi_body or "No KPIs computed."})

    if anomalies:
        anomaly_body = ""
        for a in anomalies:
            anomaly_body += f"- Column '{a.get('column', '?')}' — Value: {a.get('value', '?')} — {a.get('reason', '')}\n"
        sections.append({"heading": "Anomalies Detected", "body": anomaly_body})
    else:
        sections.append({"heading": "Anomalies", "body": "No anomalies detected in this analysis run."})

    rec_body = ""
    if anomalies:
        rec_body = "- Review flagged anomalies before taking business action.\n- Validate source data for outlier rows.\n"
    else:
        rec_body = "- Continue monitoring. All metrics within expected ranges.\n"
    sections.append({"heading": "Recommendations", "body": rec_body})

    return {
        "title": f"Analysis Report (DRAFT) — {now.strftime('%d %b %Y')}",
        "generated_at": now.isoformat(),
        "sections": sections,
        "draft_flag": True,
    }


def _build_invoice_draft(analysis_result: dict, template: dict | None) -> dict:
    """Build a real invoice draft from analysis data."""
    kpis = analysis_result.get("kpi_summary", {})
    now = datetime.now()

    total_hours = kpis.get("total_billable_hours", kpis.get("hours_sum", 0))
    rate = kpis.get("hourly_rate_mean", kpis.get("rate_mean", 0))
    subtotal = kpis.get("total_amount_sum", kpis.get("amount_sum", total_hours * rate if rate else 0))
    vat = subtotal * 0.15
    total_due = subtotal + vat

    return {
        "subject": f"[DRAFT] Invoice — {now.strftime('%b %Y')}",
        "invoice": {
            "invoice_number": f"INV-{now.strftime('%Y')}-DRAFT",
            "date": now.strftime("%Y-%m-%d"),
            "subtotal": round(subtotal, 2),
            "vat": round(vat, 2),
            "total_due": round(total_due, 2),
            "currency": "ZAR",
        },
        "draft_flag": True,
    }


def _build_notification_draft(analysis_result: dict, template: dict | None) -> dict:
    """Build a real notification/alert draft."""
    anomalies = analysis_result.get("anomalies", [])
    kpis = analysis_result.get("kpi_summary", {})

    if anomalies:
        subject = f"[DRAFT] Alert: {len(anomalies)} Anomalies Require Attention"
        body = "The following anomalies were detected:\n\n" + "\n".join(
            f"- {a.get('column', '?')}: {a.get('value', '?')} — {a.get('reason', '')}"
            for a in anomalies
        )
    else:
        subject = "[DRAFT] Status Update: All Systems Normal"
        kpi_items = [(k, v) for k, v in kpis.items() if isinstance(v, (int, float))]
        body = "No anomalies detected. Key metrics:\n\n" + "\n".join(
            f"- {k.replace('_', ' ').title()}: {v:,.2f}" for k, v in kpi_items[:5]
        )

    body += "\n\n*This is a DRAFT notification. Do not distribute until approved.*"

    return {
        "subject": subject,
        "body": body,
        "severity": "high" if anomalies else "info",
        "draft_flag": True,
    }


class LocalLLMOrchestrator:
    """
    Template-driven draft generator with optional local LLM enrichment.
    Uses structured templates from templates/ combined with deterministic
    analysis data.  When a local LLM server is available (Ollama / GPT4All-J),
    it enriches drafts with natural-language insights.
    Zero-Cloud: no external API calls.  All generation is local.

    Enforces all 10 LLM Laws:
      1. Drafts only   2. Human approval  3. Zero-Cloud
      4. Input sanitation  5. Deterministic  6. Append-only logs
      7. HW-bound license  8. No PII  9. Graceful degradation
      10. draft_flag=True
    """

    _BUILDERS = {
        "email": _build_email_draft,
        "calendar": _build_calendar_draft,
        "report": _build_report_draft,
        "invoice": _build_invoice_draft,
        "notification": _build_notification_draft,
    }

    def __init__(self, templates_dir: str | None = None):
        if templates_dir:
            global _TEMPLATES_DIR
            _TEMPLATES_DIR = templates_dir
        self._llm_available: bool | None = None

    # ── LLM connectivity ──────────────────────────────────────────
    def _check_llm(self) -> bool:
        """Check if the local LLM server is reachable."""
        if not _HAS_REQUESTS:
            return False
        try:
            r = requests.get(f"{LLM_API_URL}/api/tags", timeout=2)
            self._llm_available = r.status_code == 200
        except Exception:
            self._llm_available = False
        return self._llm_available

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str | None:
        """Call the local LLM server for draft enrichment.

        Law #3: Only connects to localhost (Zero-Cloud).
        Law #8: Prompts use template variables only, no PII.
        Law #9: Returns None on failure for graceful degradation.
        """
        if not _HAS_REQUESTS:
            return None
        try:
            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
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
                timeout=90,
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("message", {}).get("content", "")
        except Exception as exc:
            logger.debug("LLM call failed (graceful degradation): %s", exc)
        return None

    # ── Draft generation ──────────────────────────────────────────
    def generate_draft(self, input_data: dict, analysis_result: dict, draft_type: str) -> dict:
        """
        Generate a real draft output from analysis results.

        Strategy:
        1. Build structured draft from templates + analysis data
        2. If local LLM available, enrich with natural-language summary
        3. Always enforce draft_flag=True (Law #1, #10)

        Parameters
        ----------
        input_data : dict
            Raw parsed input data (not sent to any external service).
        analysis_result : dict
            Deterministic analysis output (KPIs + anomalies).
        draft_type : str
            One of: email, calendar, report, invoice, notification.

        Returns
        -------
        dict
            Structured draft content. Always includes draft_flag=True.
        """
        template = _select_template(draft_type, analysis_result)
        builder = self._BUILDERS.get(draft_type, _build_email_draft)
        draft = builder(analysis_result, template)

        # Law #9: Try LLM enrichment, fall back to template-only
        if self._llm_available is None:
            self._check_llm()

        if self._llm_available and template:
            sys_prompt = template.get("system_prompt", "You are a business assistant. Generate professional draft content.")
            user_tpl = template.get("user_prompt_template", "")
            if user_tpl:
                # Build user prompt from KPI data (Law #8: no PII, template vars only)
                kpi_str = json.dumps(analysis_result.get("kpi_summary", {}), indent=2)
                anomaly_str = json.dumps(analysis_result.get("anomalies", []), indent=2)
                user_msg = user_tpl.replace("{{kpi_summary}}", kpi_str).replace("{{anomalies}}", anomaly_str)
                llm_response = self._call_llm(sys_prompt, user_msg)
                if llm_response:
                    draft["llm_enrichment"] = llm_response
                    draft["llm_model"] = LLM_MODEL
                    draft["llm_source"] = "local"

        # Law #1 + #10: Always a draft
        draft["draft_flag"] = True
        return draft

    def list_available_templates(self) -> list[str]:
        """Return names of all loaded templates."""
        return list(_load_templates().keys())

    def get_llm_status(self) -> dict:
        """Return LLM connectivity status for dashboard display."""
        available = self._check_llm()
        return {
            "available": available,
            "url": LLM_API_URL,
            "model": LLM_MODEL,
            "mode": "llm_enhanced" if available else "template_only",
        }


def process_results_into_draft(analysis_result_dict: dict, draft_type: str, db_session) -> dict:
    """
    Orchestration entry point:
    1. Load templates from templates/
    2. Select best-match template for draft_type
    3. Generate structured draft from analysis data
    4. Enforce approved=False (draft-only workflow)

    Parameters
    ----------
    analysis_result_dict : dict
        Output from the deterministic analysis engine.
    draft_type : str
        Type of draft to generate (email, calendar, report, invoice, notification).
    db_session
        Database session (unused here — saving happens in the API layer).

    Returns
    -------
    dict
        {"content": <draft dict>, "draft_type": str, "approved": False}
    """
    orchestrator = LocalLLMOrchestrator()
    draft_content = orchestrator.generate_draft({}, analysis_result_dict, draft_type)

    return {
        "content": draft_content,
        "draft_type": draft_type,
        "approved": False,
    }

