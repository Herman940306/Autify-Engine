"""
Autify Engine V1 — Security Tests
Validates license enforcement, file access restrictions, and Zero-Cloud compliance.
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from license.manager import get_hardware_fingerprint, verify_license, LICENSE_FILE


# ── Hardware Fingerprint ──────────────────────────────────────────────

class TestHardwareFingerprint:
    def test_fingerprint_is_string(self):
        fp = get_hardware_fingerprint()
        assert isinstance(fp, str)

    def test_fingerprint_is_sha256(self):
        fp = get_hardware_fingerprint()
        assert len(fp) == 64  # SHA-256 hex digest

    def test_fingerprint_deterministic(self):
        """Same machine must produce the same fingerprint."""
        fp1 = get_hardware_fingerprint()
        fp2 = get_hardware_fingerprint()
        assert fp1 == fp2


# ── License Verification ─────────────────────────────────────────────

class TestLicenseVerification:
    def test_missing_license_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("license.manager.LICENSE_FILE", str(tmp_path / "nope.json"))
        valid, msg = verify_license()
        assert valid is False
        assert "not found" in msg.lower()

    def test_corrupt_license_file(self, tmp_path, monkeypatch):
        bad = tmp_path / "bad.json"
        bad.write_text("not json!")
        monkeypatch.setattr("license.manager.LICENSE_FILE", str(bad))
        valid, msg = verify_license()
        assert valid is False

    def test_fingerprint_mismatch(self, tmp_path, monkeypatch):
        lic = tmp_path / "license.json"
        lic.write_text(json.dumps({"fingerprint": "wrong_fingerprint_value"}))
        monkeypatch.setattr("license.manager.LICENSE_FILE", str(lic))
        valid, msg = verify_license()
        assert valid is False
        assert "mismatch" in msg.lower()

    def test_valid_license(self, tmp_path, monkeypatch):
        fp = get_hardware_fingerprint()
        lic = tmp_path / "license.json"
        lic.write_text(json.dumps({"fingerprint": fp}))
        monkeypatch.setattr("license.manager.LICENSE_FILE", str(lic))
        valid, msg = verify_license()
        assert valid is True


# ── Zero-Cloud Compliance ─────────────────────────────────────────────

class TestZeroCloudCompliance:
    def test_no_external_urls_in_api(self):
        """Scan the api/main.py for any hardcoded external URLs."""
        api_path = os.path.join(os.path.dirname(__file__), '..', '..', 'api', 'main.py')
        with open(api_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Should not contain external API calls
        external_indicators = ['https://api.', 'https://cloud.', 'amazonaws.com', 'googleapis.com']
        for indicator in external_indicators:
            assert indicator not in content, f"External URL detected: {indicator}"

    def test_no_external_urls_in_orchestrator(self):
        """Scan the LLM orchestrator for external API endpoints."""
        orch_path = os.path.join(os.path.dirname(__file__), '..', '..', 'llm', 'orchestrator.py')
        with open(orch_path, 'r', encoding='utf-8') as f:
            content = f.read()
        external_indicators = ['https://api.openai.com', 'https://cloud.', 'anthropic.com']
        for indicator in external_indicators:
            assert indicator not in content, f"External LLM URL detected: {indicator}"


# ── Draft-Only Cannot Be Bypassed ────────────────────────────────────

class TestDraftOnlyEnforcement:
    def test_draft_type_field_cannot_bypass_approval(self):
        """The DraftOutput model's approved field defaults to False."""
        from database.models import DraftOutput
        draft = DraftOutput()
        assert draft.approved is False or draft.approved is None
