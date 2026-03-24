"""
Report writer — converts ProfileResult and model results into markdown reports.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from src.eda.profiler import run_profile, ProfileResult
from src.ingest.csv_loader import DB_PATH, CONFIG_PATH


REPORTS_DIR = "outputs/reports"


def _load_config(config_path: str = CONFIG_PATH) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def write_report(db_path: str = DB_PATH, config_path: str = CONFIG_PATH) -> str:
    """Run profiler and write EDA markdown report. Returns report path."""
    profile = run_profile(db_path=db_path, config_path=config_path)
    cfg = _load_config(config_path)
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)

    lines = [
        f"# EDA Report — {cfg['project']['name']}",
        f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        "## Dataset Overview",
        f"| | |",
        f"|---|---|",
        f"| Rows | {profile.row_count:,} |",
        f"| Columns | {profile.col_count} |",
        f"| Duplicate rows | {profile.duplicate_rows:,} |",
        f"| Mode | {cfg.get('mode', 'unknown')} |",
        "",
    ]

    if profile.target_balance:
        lines += [
            f"## Target Column: `{profile.target_column}`",
            "| Value | Count | % |",
            "|-------|-------|---|",
        ]
        total = sum(profile.target_balance.values())
        for val, count in profile.target_balance.items():
            pct = round(count / total * 100, 1)
            lines.append(f"| {val} | {count:,} | {pct}% |")
        lines.append("")

    if profile.high_null_columns:
        lines += [
            "## ⚠️ High Null Columns (>20%)",
            ", ".join(f"`{c}`" for c in profile.high_null_columns),
            "",
        ]

    if profile.constant_columns:
        lines += [
            "## ⚠️ Constant Columns (1 unique value — likely useless as features)",
            ", ".join(f"`{c}`" for c in profile.constant_columns),
            "",
        ]

    lines += [
        "## Column Profiles",
        "| Column | Type | Nulls | Unique | Min | Max | Mean | Samples |",
        "|--------|------|-------|--------|-----|-----|------|---------|",
    ]
    for p in profile.columns:
        samples_str = ", ".join(p.sample_values[:3])
        lines.append(
            f"| {p.name} | {p.dtype} | {p.null_pct}% | {p.n_unique:,} "
            f"| {p.min_val or '—'} | {p.max_val or '—'} | {p.mean_val or '—'} | {samples_str} |"
        )

    report_path = f"{REPORTS_DIR}/eda_report.md"
    Path(report_path).write_text("\n".join(lines))
    return report_path


def write_client_report(
    db_path: str = DB_PATH,
    config_path: str = CONFIG_PATH,
    model_results_path: str | None = None,
) -> str:
    """Write a client-facing summary combining EDA + model results."""
    profile = run_profile(db_path=db_path, config_path=config_path)
    cfg = _load_config(config_path)
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Client Report — {cfg['project']['name']}",
        f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        "## Executive Summary",
        f"Analysis of **{profile.row_count:,} records** across **{profile.col_count} features**.",
        "",
        "## Data Quality",
    ]

    if profile.high_null_columns:
        lines.append(f"- **Columns with >20% missing data:** {', '.join(profile.high_null_columns)}")
    if profile.duplicate_rows > 0:
        lines.append(f"- **Duplicate rows found:** {profile.duplicate_rows:,} — recommend deduplication")
    if not profile.high_null_columns and profile.duplicate_rows == 0:
        lines.append("- No major data quality issues found.")

    lines += ["", "## Model Results"]

    if model_results_path and Path(model_results_path).exists():
        lines.append(Path(model_results_path).read_text())
    else:
        lines.append("_Run **/model** to generate model results, then re-run **/report**._")

    lines += [
        "",
        "## Recommended Next Steps",
        "1. Review the top features above with domain experts to confirm they make business sense.",
        "2. Run **/fullrun** to train on the complete dataset for production-grade metrics.",
        "3. Run **/promote** to save the model and prepare for deployment.",
    ]

    report_path = f"{REPORTS_DIR}/client_report.md"
    Path(report_path).write_text("\n".join(lines))
    return report_path
