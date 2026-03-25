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
    """Run profiler and write deep EDA markdown report. Returns report path."""
    profile = run_profile(db_path=db_path, config_path=config_path)
    cfg = _load_config(config_path)
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)

    lines = [
        f"# EDA Report — {cfg['project']['name']}",
        f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        "## Dataset Overview",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Rows | {profile.row_count:,} |",
        f"| Columns | {profile.col_count} |",
        f"| Numeric columns | {len(profile.numeric_columns)} |",
        f"| Categorical columns | {len(profile.categorical_columns)} |",
        f"| Date columns | {len(profile.date_columns)} |",
        f"| Duplicate rows | {profile.duplicate_rows:,} |",
        f"| Mode | {cfg.get('mode', 'unknown')} |",
        "",
    ]

    # --- Recommendations (top of report — most actionable) ---
    if profile.recommendations:
        lines += ["## Recommendations", ""]
        for i, rec in enumerate(profile.recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    # --- Target analysis ---
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

    # --- Target-feature relationships ---
    if profile.target_relationships:
        lines += ["## Feature-Target Relationships", ""]
        for rel in profile.target_relationships:
            if rel.relationship_type == "numeric_means":
                lines.append(f"**{rel.feature}** (mean by target):")
                for target_val, mean in rel.detail.items():
                    lines.append(f"  - {profile.target_column}={target_val}: mean={mean}")
            elif rel.relationship_type == "category_rates":
                lines.append(f"**{rel.feature}** (positive rate by category):")
                for cat, rate in sorted(rel.detail.items(), key=lambda x: -x[1]):
                    lines.append(f"  - {cat}: {rate:.1%}")
            lines.append("")

    # --- Correlations ---
    if profile.correlations:
        lines += [
            "## Top Correlations",
            "| Feature A | Feature B | Pearson r |",
            "|-----------|-----------|-----------|",
        ]
        for c in profile.correlations[:10]:
            strength = ""
            if abs(c.pearson) > 0.8:
                strength = " **strong**"
            elif abs(c.pearson) > 0.5:
                strength = " moderate"
            lines.append(f"| {c.col_a} | {c.col_b} | {c.pearson:.4f}{strength} |")
        lines.append("")

    # --- Data quality flags ---
    quality_issues = []
    if profile.high_null_columns:
        quality_issues.append(
            "**High nulls (>20%):** " + ", ".join(f"`{c}`" for c in profile.high_null_columns)
        )
    if profile.constant_columns:
        quality_issues.append(
            "**Constant columns (useless):** " + ", ".join(f"`{c}`" for c in profile.constant_columns)
        )
    if profile.high_cardinality_columns:
        quality_issues.append(
            "**High cardinality (likely IDs):** " + ", ".join(f"`{c}`" for c in profile.high_cardinality_columns)
        )
    if profile.outlier_columns:
        quality_issues.append(
            "**Outlier-heavy (>5% outside IQR):** " + ", ".join(f"`{c}`" for c in profile.outlier_columns)
        )

    if quality_issues:
        lines += ["## Data Quality Flags", ""]
        lines += quality_issues
        lines.append("")

    # --- Column profiles ---
    lines += [
        "## Column Profiles",
        "| Column | Type | Nulls | Unique | Min | Max | Mean | Median | Std | Skew | Outliers |",
        "|--------|------|-------|--------|-----|-----|------|--------|-----|------|----------|",
    ]
    for p in profile.columns:
        lines.append(
            f"| {p.name} | {p.dtype} | {p.null_pct}% | {p.n_unique:,} "
            f"| {p.min_val or '—'} | {p.max_val or '—'} "
            f"| {p.mean_val or '—'} | {p.median_val or '—'} "
            f"| {p.std_val or '—'} | {p.skewness or '—'} "
            f"| {p.outlier_pct}% |"
        )
    lines.append("")

    # --- Categorical breakdowns ---
    cat_profiles = [p for p in profile.columns if p.name in profile.categorical_columns and p.n_unique <= 20]
    if cat_profiles:
        lines += ["## Categorical Distributions", ""]
        for p in cat_profiles:
            lines.append(f"**{p.name}** ({p.n_unique} values): {', '.join(p.sample_values[:5])}")
        lines.append("")

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
        f"Analysis of **{profile.row_count:,} records** across **{profile.col_count} features** "
        f"({len(profile.numeric_columns)} numeric, {len(profile.categorical_columns)} categorical).",
        "",
    ]

    # Data quality summary
    lines += ["## Data Quality", ""]
    if profile.recommendations:
        for rec in profile.recommendations[:5]:
            lines.append(f"- {rec}")
    else:
        lines.append("- No major data quality issues found.")
    lines.append("")

    # Key findings from correlations
    if profile.correlations:
        strong = [c for c in profile.correlations if abs(c.pearson) > 0.5]
        if strong:
            lines += ["## Key Relationships", ""]
            for c in strong[:5]:
                direction = "positively" if c.pearson > 0 else "negatively"
                lines.append(f"- **{c.col_a}** and **{c.col_b}** are {direction} correlated (r={c.pearson:.2f})")
            lines.append("")

    # Target insights
    if profile.target_relationships:
        lines += ["## What Drives the Target", ""]
        for rel in profile.target_relationships[:5]:
            if rel.relationship_type == "numeric_means":
                vals = list(rel.detail.values())
                if len(vals) >= 2 and vals[0] != 0:
                    diff_pct = abs(vals[-1] - vals[0]) / abs(vals[0]) * 100
                    lines.append(
                        f"- **{rel.feature}**: {diff_pct:.0f}% difference between target groups"
                    )
            elif rel.relationship_type == "category_rates":
                rates = sorted(rel.detail.values())
                if rates:
                    lines.append(
                        f"- **{rel.feature}**: positive rate ranges from {rates[0]:.1%} to {rates[-1]:.1%}"
                    )
        lines.append("")

    # Model results
    lines += ["## Model Results", ""]
    if model_results_path and Path(model_results_path).exists():
        lines.append(Path(model_results_path).read_text())
    else:
        lines.append("_Run **/model** to generate model results, then re-run **/report**._")

    lines += [
        "",
        "## Recommended Next Steps",
        "1. Review the top features above with domain experts — do they make business sense?",
        "2. Run **/fullrun** to train on the complete dataset for production-grade metrics.",
        "3. Run **/promote** to save the model and prepare for deployment.",
    ]

    report_path = f"{REPORTS_DIR}/client_report.md"
    Path(report_path).write_text("\n".join(lines))
    return report_path
