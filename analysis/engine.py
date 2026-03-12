"""Autify Engine V1 — Deterministic Analysis Engine.

Purely deterministic: KPIs, trends, anomalies.
No randomness, no LLM calls.  Runs identically every time on the same data.
"""

import pandas as pd
import numpy as np


def run_analysis(parsed_data: list[dict] | dict) -> dict:
    """Analyse structured JSON and return KPIs + anomalies.

    Parameters
    ----------
    parsed_data : list[dict] | dict
        Output from a parser — either tabular rows or a text dict.

    Returns
    -------
    dict  {"kpi_summary": {...}, "anomalies": [...]}
    """
    # ── Text branch (PDF / TXT) ─────────────────────────────────────
    if isinstance(parsed_data, dict) and ("parsed_text" in parsed_data or "raw_text" in parsed_data):
        text = parsed_data.get("parsed_text", parsed_data.get("raw_text", ""))
        words = text.split()
        return {
            "kpi_summary": {
                "word_count": len(words),
                "line_count": text.count("\n") + 1,
                "char_count": len(text),
            },
            "anomalies": [],
        }

    # ── Tabular branch ──────────────────────────────────────────────
    if isinstance(parsed_data, dict):
        parsed_data = [parsed_data]

    df = pd.DataFrame(parsed_data)

    kpi_summary: dict = {}
    anomalies: list[dict] = []

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    kpi_summary["row_count"] = int(len(df))
    kpi_summary["column_count"] = int(len(df.columns))

    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue

        kpi_summary[f"{col}_mean"] = float(series.mean())
        kpi_summary[f"{col}_sum"]  = float(series.sum())
        kpi_summary[f"{col}_min"]  = float(series.min())
        kpi_summary[f"{col}_max"]  = float(series.max())

        # Anomaly detection: Z-score > 3
        mean = series.mean()
        std  = series.std()
        if std > 0:
            z_scores = (series - mean).abs() / std
            outlier_mask = z_scores > 3
            for idx in series[outlier_mask].index:
                anomalies.append({
                    "column": str(col),
                    "index":  int(idx),
                    "value":  float(series[idx]),
                    "reason":  f"Z-score > 3 (Mean: {mean:.2f}, Std: {std:.2f})",
                })

    return {"kpi_summary": kpi_summary, "anomalies": anomalies}

