"""
EDA profiler — deep data quality, distributions, correlations, outliers, and target analysis.
Outputs a ProfileResult dataclass consumed by report.py.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import yaml

from src.ingest.csv_loader import get_connection, DB_PATH, CONFIG_PATH


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    null_count: int
    null_pct: float
    n_unique: int
    sample_values: list
    min_val: str | None = None
    max_val: str | None = None
    mean_val: float | None = None
    median_val: float | None = None
    std_val: float | None = None
    p25: float | None = None
    p75: float | None = None
    skewness: float | None = None
    outlier_count: int = 0          # rows outside 1.5×IQR
    outlier_pct: float = 0.0
    cardinality_ratio: float = 0.0  # n_unique / row_count — flags ID-like columns


@dataclass
class Correlation:
    col_a: str
    col_b: str
    pearson: float


@dataclass
class TargetRelationship:
    """How a feature relates to the target column."""
    feature: str
    relationship_type: str  # "numeric_means" or "category_rates"
    detail: dict            # e.g., {"0": 0.32, "1": 0.68} for mean by target


@dataclass
class ProfileResult:
    row_count: int
    col_count: int
    columns: list[ColumnProfile]
    duplicate_rows: int
    high_null_columns: list[str]        # >20% null
    constant_columns: list[str]         # 1 unique value
    high_cardinality_columns: list[str] # >90% unique (likely IDs)
    correlations: list[Correlation]     # top correlated pairs
    target_column: str | None = None
    target_balance: dict | None = None
    target_relationships: list[TargetRelationship] = field(default_factory=list)
    numeric_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)
    date_columns: list[str] = field(default_factory=list)
    outlier_columns: list[str] = field(default_factory=list)  # columns with >5% outliers
    recommendations: list[str] = field(default_factory=list)  # actionable EDA findings


def _is_numeric(dtype: str) -> bool:
    return any(t in dtype.upper() for t in (
        "INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "BIGINT", "HUGEINT",
    ))


def _is_date(dtype: str) -> bool:
    return any(t in dtype.upper() for t in ("DATE", "TIMESTAMP", "TIME"))


def run_profile(db_path: str = DB_PATH, config_path: str = CONFIG_PATH) -> ProfileResult:
    """Deep-profile main_data table and return a ProfileResult."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    con = get_connection(db_path)
    row_count = con.execute("SELECT COUNT(*) FROM main_data").fetchone()[0]
    duplicate_rows = row_count - con.execute(
        "SELECT COUNT(*) FROM (SELECT DISTINCT * FROM main_data)"
    ).fetchone()[0]

    col_info = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name='main_data' ORDER BY ordinal_position"
    ).fetchall()

    profiles = []
    numeric_cols = []
    categorical_cols = []
    date_cols = []

    for col, dtype in col_info:
        null_count = con.execute(
            f'SELECT COUNT(*) FROM main_data WHERE "{col}" IS NULL'
        ).fetchone()[0]
        null_pct = round(null_count / row_count * 100, 1) if row_count > 0 else 0
        n_unique = con.execute(
            f'SELECT COUNT(DISTINCT "{col}") FROM main_data'
        ).fetchone()[0]
        samples = [
            str(r[0]) for r in con.execute(
                f'SELECT DISTINCT "{col}" FROM main_data WHERE "{col}" IS NOT NULL LIMIT 5'
            ).fetchall()
        ]
        cardinality_ratio = round(n_unique / row_count, 4) if row_count > 0 else 0

        min_val = max_val = mean_val = median_val = std_val = None
        p25 = p75 = skewness = None
        outlier_count = 0
        outlier_pct = 0.0

        is_num = _is_numeric(dtype)
        is_dt = _is_date(dtype)

        if is_num:
            numeric_cols.append(col)
            stats = con.execute(f"""
                SELECT
                    MIN("{col}"), MAX("{col}"), AVG("{col}"),
                    MEDIAN("{col}"), STDDEV("{col}"),
                    QUANTILE_CONT("{col}", 0.25),
                    QUANTILE_CONT("{col}", 0.75)
                FROM main_data
            """).fetchone()
            min_val = str(stats[0]) if stats[0] is not None else None
            max_val = str(stats[1]) if stats[1] is not None else None
            mean_val = round(float(stats[2]), 4) if stats[2] is not None else None
            median_val = round(float(stats[3]), 4) if stats[3] is not None else None
            std_val = round(float(stats[4]), 4) if stats[4] is not None else None
            p25 = round(float(stats[5]), 4) if stats[5] is not None else None
            p75 = round(float(stats[6]), 4) if stats[6] is not None else None

            # Skewness: (mean - median) / std as quick approximation
            if std_val and std_val > 0 and mean_val is not None and median_val is not None:
                skewness = round((mean_val - median_val) / std_val, 4)

            # Outlier detection: IQR method
            if p25 is not None and p75 is not None:
                iqr = p75 - p25
                lower = p25 - 1.5 * iqr
                upper = p75 + 1.5 * iqr
                outlier_count = con.execute(f"""
                    SELECT COUNT(*) FROM main_data
                    WHERE "{col}" IS NOT NULL AND ("{col}" < {lower} OR "{col}" > {upper})
                """).fetchone()[0]
                outlier_pct = round(outlier_count / row_count * 100, 1) if row_count > 0 else 0

        elif is_dt:
            date_cols.append(col)
            try:
                dr = con.execute(f'SELECT MIN("{col}"), MAX("{col}") FROM main_data').fetchone()
                min_val, max_val = str(dr[0]), str(dr[1])
            except Exception:
                pass
        else:
            categorical_cols.append(col)

        profiles.append(ColumnProfile(
            name=col, dtype=dtype, null_count=null_count, null_pct=null_pct,
            n_unique=n_unique, sample_values=samples,
            min_val=min_val, max_val=max_val, mean_val=mean_val,
            median_val=median_val, std_val=std_val, p25=p25, p75=p75,
            skewness=skewness, outlier_count=outlier_count, outlier_pct=outlier_pct,
            cardinality_ratio=cardinality_ratio,
        ))

    high_null = [p.name for p in profiles if p.null_pct > 20]
    constant = [p.name for p in profiles if p.n_unique <= 1]
    high_card = [p.name for p in profiles if p.cardinality_ratio > 0.9 and p.n_unique > 10]
    outlier_cols = [p.name for p in profiles if p.outlier_pct > 5]

    # --- Correlations (top pairs by absolute Pearson) ---
    correlations = []
    if len(numeric_cols) >= 2:
        pairs_sql = []
        seen = set()
        for i, a in enumerate(numeric_cols):
            for b in numeric_cols[i + 1:]:
                key = tuple(sorted([a, b]))
                if key not in seen:
                    seen.add(key)
                    pairs_sql.append(
                        f'CORR("{a}", "{b}") AS corr_{"_".join(key)}'
                    )
        if pairs_sql:
            try:
                # DuckDB can compute all correlations in one pass
                results = con.execute(f"SELECT {', '.join(pairs_sql)} FROM main_data").fetchone()
                idx = 0
                for i, a in enumerate(numeric_cols):
                    for b in numeric_cols[i + 1:]:
                        val = results[idx]
                        if val is not None and not math.isnan(val):
                            correlations.append(Correlation(
                                col_a=a, col_b=b, pearson=round(val, 4),
                            ))
                        idx += 1
                correlations.sort(key=lambda c: abs(c.pearson), reverse=True)
                correlations = correlations[:15]  # top 15 pairs
            except Exception:
                pass

    # --- Target analysis ---
    target_col = cfg.get("supervised", {}).get("target_column")
    target_balance = None
    target_relationships: list[TargetRelationship] = []

    if target_col and cfg.get("mode") == "supervised":
        try:
            rows = con.execute(
                f'SELECT "{target_col}", COUNT(*) as n FROM main_data '
                f'GROUP BY "{target_col}" ORDER BY n DESC'
            ).fetchall()
            target_balance = {str(r[0]): r[1] for r in rows}
        except Exception:
            pass

        # Feature-target relationships
        for col in numeric_cols:
            if col == target_col:
                continue
            try:
                means = con.execute(f"""
                    SELECT "{target_col}", AVG("{col}") as avg_val, COUNT(*) as n
                    FROM main_data
                    GROUP BY "{target_col}"
                    ORDER BY "{target_col}"
                """).fetchall()
                detail = {str(r[0]): round(float(r[1]), 4) for r in means if r[1] is not None}
                if detail:
                    target_relationships.append(TargetRelationship(
                        feature=col, relationship_type="numeric_means", detail=detail,
                    ))
            except Exception:
                pass

        for col in categorical_cols:
            if col == target_col:
                continue
            try:
                rates = con.execute(f"""
                    SELECT "{col}",
                           COUNT(*) as total,
                           SUM(CASE WHEN CAST("{target_col}" AS VARCHAR) IN ('1','true','True','yes') THEN 1 ELSE 0 END) as positive
                    FROM main_data
                    GROUP BY "{col}"
                    HAVING COUNT(*) >= 10
                    ORDER BY total DESC
                    LIMIT 10
                """).fetchall()
                detail = {str(r[0]): round(r[2] / r[1], 4) if r[1] > 0 else 0 for r in rates}
                if detail:
                    target_relationships.append(TargetRelationship(
                        feature=col, relationship_type="category_rates", detail=detail,
                    ))
            except Exception:
                pass

    # --- Recommendations ---
    recommendations = []
    if duplicate_rows > 0:
        recommendations.append(
            f"Deduplicate: {duplicate_rows:,} duplicate rows found ({duplicate_rows/row_count*100:.1f}%). "
            "Consider whether these are real duplicates or repeat transactions."
        )
    if high_null:
        recommendations.append(
            f"Handle missing data: {', '.join(high_null)} have >20% nulls. "
            "Decide per-column: impute (median/mode), flag as indicator, or drop."
        )
    if high_card:
        recommendations.append(
            f"High-cardinality columns: {', '.join(high_card)} are likely IDs or free-text. "
            "Exclude from modeling or engineer features from them."
        )
    if outlier_cols:
        recommendations.append(
            f"Outliers detected in: {', '.join(outlier_cols)}. "
            "Investigate — could be data errors, or genuine extreme values worth keeping."
        )
    strong_corr = [c for c in correlations if abs(c.pearson) > 0.8]
    if strong_corr:
        pairs = [f"{c.col_a}↔{c.col_b} ({c.pearson:.2f})" for c in strong_corr[:3]]
        recommendations.append(
            f"Strongly correlated features: {', '.join(pairs)}. "
            "Consider dropping one from each pair to avoid multicollinearity."
        )
    if target_balance:
        vals = list(target_balance.values())
        if len(vals) >= 2:
            minority_pct = min(vals) / sum(vals) * 100
            if minority_pct < 10:
                recommendations.append(
                    f"Class imbalance: minority class is {minority_pct:.1f}% of data. "
                    "Consider SMOTE, class weights, or stratified sampling."
                )

    for p in profiles:
        if p.skewness is not None and abs(p.skewness) > 1:
            direction = "right" if p.skewness > 0 else "left"
            recommendations.append(
                f"Skewed distribution: {p.name} is {direction}-skewed ({p.skewness:.2f}). "
                "Consider log transform for modeling."
            )

    # Cap at 10 most important recommendations
    recommendations = recommendations[:10]

    con.close()
    return ProfileResult(
        row_count=row_count, col_count=len(profiles), columns=profiles,
        duplicate_rows=duplicate_rows, high_null_columns=high_null,
        constant_columns=constant, high_cardinality_columns=high_card,
        correlations=correlations, target_column=target_col,
        target_balance=target_balance, target_relationships=target_relationships,
        numeric_columns=numeric_cols, categorical_columns=categorical_cols,
        date_columns=date_cols, outlier_columns=outlier_cols,
        recommendations=recommendations,
    )
