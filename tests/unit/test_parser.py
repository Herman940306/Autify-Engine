"""
Autify Engine V1 — Unit Tests: Parser Module
Tests all supported input formats are correctly converted to structured JSON.
"""

import os
import json
import tempfile
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from parsers.parser import parse_file


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def csv_file(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("name,age,revenue\nAlice,30,15000\nBob,25,22000\nCarla,40,18000\n")
    return str(p)


@pytest.fixture
def json_file(tmp_path):
    data = [{"product": "Widget", "qty": 10}, {"product": "Gadget", "qty": 5}]
    p = tmp_path / "test.json"
    p.write_text(json.dumps(data))
    return str(p)


@pytest.fixture
def txt_file(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("This is a plain text test file with some content.")
    return str(p)


# ── CSV Tests ─────────────────────────────────────────────────────────

class TestCSVParser:
    def test_csv_returns_list(self, csv_file):
        result = parse_file(csv_file, "csv")
        assert isinstance(result, list)

    def test_csv_row_count(self, csv_file):
        result = parse_file(csv_file, "csv")
        assert len(result) == 3

    def test_csv_columns(self, csv_file):
        result = parse_file(csv_file, "csv")
        assert "name" in result[0]
        assert "age" in result[0]
        assert "revenue" in result[0]

    def test_csv_values(self, csv_file):
        result = parse_file(csv_file, "csv")
        assert result[0]["name"] == "Alice"
        assert result[1]["revenue"] == 22000


# ── JSON Tests ────────────────────────────────────────────────────────

class TestJSONParser:
    def test_json_returns_list(self, json_file):
        result = parse_file(json_file, "json")
        assert isinstance(result, list)

    def test_json_row_count(self, json_file):
        result = parse_file(json_file, "json")
        assert len(result) == 2

    def test_json_values(self, json_file):
        result = parse_file(json_file, "json")
        assert result[0]["product"] == "Widget"


# ── TXT Tests ─────────────────────────────────────────────────────────

class TestTXTParser:
    def test_txt_returns_dict(self, txt_file):
        result = parse_file(txt_file, "txt")
        assert isinstance(result, dict)
        assert "raw_text" in result

    def test_txt_content(self, txt_file):
        result = parse_file(txt_file, "txt")
        assert "plain text" in result["raw_text"]


# ── Error handling ────────────────────────────────────────────────────

class TestParserErrors:
    def test_unsupported_format(self, tmp_path):
        p = tmp_path / "test.xyz"
        p.write_text("data")
        with pytest.raises(ValueError, match="Unsupported"):
            parse_file(str(p), "xyz")
