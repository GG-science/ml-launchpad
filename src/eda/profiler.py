"""
EDA profiler — runs data quality + distribution analysis on main_data in DuckDB.
Outputs a ProfileResult dataclass consumed by report.py.
"""
from __future__ import annotations

import json
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


@dataclass
class ProfileResult:
    row_count: int
    col_count: int
    columns: list[ColumnProfile]
    duplicate_rows: int
    high_null_columns: list[str]    # >20% null
    constant_columns: list[str]     # 1 unique value
    target_column: str | None = None
    target_balance: dict | None = None  # for classification targets


def run_profile(db_path: str = DB_PATH, config_path: str = CONFIG_PATH) -> ProfileResult:
    """Profile main_data table and return a ProfileResult."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    con = get_connection(db_path)
    row_count = con.execute("SELECT COUNT(*) FROM main_data").fetchone()[0]
    duplicate_rows = row_count - con.execute("SELECT COUNT(*) FROM (SELECT DISTINCT * FROM main_data)").fetchone()[0]

    col_info = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='main_data' ORDER BY ordinal_position"
    ).fetchall()

    profiles = []
    for col, dtype in col_info:
        null_count = con.execute(f'SELECT COUNT(*) FROM main_data WHERE "{col}" IS NULL').fetchone()[0]
        null_pct = round(null_count / row_count * 100, 1) if row_count > 0 else 0
        n_unique = con.execute(f'SELECT COUNT(DISTINCT "{col}") FROM main_data').fetchone()[0]
        samples = [
            str(r[0]) for r in con.execute(
                f'SELECT DISTINCT "{col}" FROM main_data WHERE "{col}" IS NOT NULL LIMIT 5'
            ).fetchall()
        ]

        min_val = max_val = mean_val = None
        is_numeric = any(t in dtype.upper() for t in ("INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "BIGINT", "HUGEINT"))
        if is_numeric:
            stats = con.execute(
                f'SELECT MIN("{col}"), MAX("{col}"), AVG("{col}") FROM main_data'
            ).fetchone()
            min_val, max_val = str(stats[0]), str(stats[1])
            mean_val = round(float(stats[2]), 4) if stats[2] is not None else None

        profiles.append(ColumnProfile(
            name=col, dtype=dtype, null_count=null_count, null_pct=null_pct,
            n_unique=n_unique, sample_values=samples,
            min_val=min_val, max_val=max_val, mean_val=mean_val,
        ))

    high_null = [p.name for p in profiles if p.null_pct > 20]
    constant = [p.name for p in profiles if p.n_unique <= 1]

    target_col = cfg.get("supervised", {}).get("target_column")
    target_balance = None
    if target_col and cfg.get("mode") == "supervised":
        try:
            rows = con.execute(
                f'SELECT "{target_col}", COUNT(*) as n FROM main_data GROUP BY "{target_col}" ORDER BY n DESC'
            ).fetchall()
            target_balance = {str(r[0]): r[1] for r in rows}
        except Exception:
            pass

    con.close()
    return ProfileResult(
        row_count=row_count, col_count=len(profiles), columns=profiles,
        duplicate_rows=duplicate_rows, high_null_columns=high_null,
        constant_columns=constant, target_column=target_col,
        target_balance=target_balance,
    )
