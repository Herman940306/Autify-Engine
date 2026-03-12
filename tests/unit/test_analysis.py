"""
Autify Engine V1 — Unit Tests: Deterministic Analysis Engine
Validates KPI calculations and anomaly detection are purely deterministic.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis.engine import run_analysis


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def sales_data():
    return [
        {"product": "Widget", "revenue": 1000, "units": 10},
        {"product": "Gadget", "revenue": 2000, "units": 15},
        {"product": "Gizmo",  "revenue": 1500, "units": 12},
        {"product": "Doohickey", "revenue": 800, "units": 8},
    ]


@pytest.fixture
def data_with_outlier():
    """Dataset with enough points for Z-score > 3 to detect the outlier.

    With ~30 normal values around 100 and one extreme value (9999),
    the Z-score of 9999 comfortably exceeds 3.
    """
    normal = [{"revenue": v} for v in [
        100, 110, 105, 95, 100, 102, 98, 100, 99, 103,
        97, 101, 104, 96, 108, 92, 106, 94, 107, 93,
        101, 99, 102, 98, 100, 103, 97, 105, 95, 100,
    ]]
    normal.append({"revenue": 9999})  # outlier
    return normal


@pytest.fixture
def text_data():
    return {"parsed_text": "This is a sample document with some words in it."}


# ── KPI Tests ─────────────────────────────────────────────────────────

class TestKPICalculation:
    def test_returns_dict(self, sales_data):
        result = run_analysis(sales_data)
        assert isinstance(result, dict)
        assert "kpi_summary" in result
        assert "anomalies" in result

    def test_sum_kpi(self, sales_data):
        result = run_analysis(sales_data)
        kpis = result["kpi_summary"]
        assert kpis["revenue_sum"] == 5300
        assert kpis["units_sum"] == 45

    def test_mean_kpi(self, sales_data):
        result = run_analysis(sales_data)
        kpis = result["kpi_summary"]
        assert kpis["revenue_mean"] == pytest.approx(1325.0)
        assert kpis["units_mean"] == pytest.approx(11.25)

    def test_determinism(self, sales_data):
        """Running analysis twice must give identical results."""
        r1 = run_analysis(sales_data)
        r2 = run_analysis(sales_data)
        assert r1 == r2


# ── Anomaly Tests ─────────────────────────────────────────────────────

class TestAnomalyDetection:
    def test_detects_outlier(self, data_with_outlier):
        result = run_analysis(data_with_outlier)
        assert len(result["anomalies"]) >= 1
        outlier = result["anomalies"][0]
        assert outlier["value"] == 9999
        assert "Z-score" in outlier["reason"]

    def test_no_anomalies_in_clean_data(self, sales_data):
        result = run_analysis(sales_data)
        assert len(result["anomalies"]) == 0


# ── Text input branch ────────────────────────────────────────────────

class TestTextAnalysis:
    def test_text_returns_word_count(self, text_data):
        result = run_analysis(text_data)
        assert "kpi_summary" in result
        assert "anomalies" in result
        assert result["kpi_summary"]["word_count"] > 0
        assert result["kpi_summary"]["line_count"] >= 1
        assert result["kpi_summary"]["char_count"] > 0

    def test_text_with_raw_text_key(self):
        data = {"raw_text": "Hello world this is raw text input"}
        result = run_analysis(data)
        assert "kpi_summary" in result
        assert result["kpi_summary"]["word_count"] == 7
