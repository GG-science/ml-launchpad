"""
Schema registry — stores column metadata in DuckDB for use by EDA and model layers.
Table: schema_registry (csv_path, column_name, dtype, null_count, sample_values)
"""
from __future__ import annotations

import json
import duckdb
from pathlib import Path

from src.ingest.csv_loader import get_connection, DB_PATH


def register_schema(csv_path: str, db_path: str = DB_PATH) -> None:
    """Read schema from main_data and write to schema_registry table."""
    con = get_connection(db_path)

    con.execute("""
        CREATE TABLE IF NOT EXISTS schema_registry (
            csv_path      VARCHAR,
            column_name   VARCHAR,
            dtype         VARCHAR,
            null_count    BIGINT,
            sample_values VARCHAR,
            registered_at TIMESTAMP DEFAULT current_timestamp,
            PRIMARY KEY (csv_path, column_name)
        )
    """)

    # Remove old entries for this csv_path
    con.execute("DELETE FROM schema_registry WHERE csv_path = ?", [csv_path])

    columns = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='main_data'"
    ).fetchall()

    for col, dtype in columns:
        null_count = con.execute(
            f"SELECT COUNT(*) FROM main_data WHERE \"{col}\" IS NULL"
        ).fetchone()[0]

        try:
            samples = con.execute(
                f"SELECT DISTINCT \"{col}\" FROM main_data WHERE \"{col}\" IS NOT NULL LIMIT 5"
            ).fetchall()
            sample_values = json.dumps([str(r[0]) for r in samples])
        except Exception:
            sample_values = "[]"

        con.execute(
            "INSERT OR REPLACE INTO schema_registry VALUES (?, ?, ?, ?, ?, current_timestamp)",
            [csv_path, col, dtype, null_count, sample_values],
        )

    con.close()


def get_schema(db_path: str = DB_PATH) -> list[dict]:
    """Return registered schema as a list of column dicts."""
    con = get_connection(db_path)
    rows = con.execute(
        "SELECT column_name, dtype, null_count, sample_values FROM schema_registry ORDER BY column_name"
    ).fetchall()
    con.close()
    return [
        {"column": r[0], "dtype": r[1], "null_count": r[2], "sample_values": json.loads(r[3])}
        for r in rows
    ]
