"""
CSV → DuckDB ingestion.
Loads a CSV (with optional row limit) into DuckDB as the 'main_data' table.
Also registers schema metadata via schema_registry.
"""
from __future__ import annotations

import duckdb
import yaml
from pathlib import Path


DB_PATH = "data/processed/store.duckdb"
CONFIG_PATH = "config/project.yml"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_connection(db_path: str = DB_PATH) -> duckdb.DuckDBPyConnection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(db_path)


def load_csv(
    csv_path: str | None = None,
    row_limit: int | None = None,
    db_path: str = DB_PATH,
) -> dict:
    """
    Load a CSV into DuckDB as 'main_data'.

    Args:
        csv_path: Path to CSV. If None, reads from config.
        row_limit: Max rows to load. If None, reads sample_row_limit from config.
        db_path: DuckDB database path.

    Returns:
        dict with keys: rows_loaded, columns, db_path
    """
    cfg = _load_config()

    if csv_path is None:
        csv_path = cfg["data"]["csv_path"]
    if row_limit is None:
        row_limit = cfg["data"].get("sample_row_limit", 50_000)

    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    con = get_connection(db_path)

    limit_clause = f"LIMIT {row_limit}" if row_limit else ""
    con.execute(f"""
        CREATE OR REPLACE TABLE main_data AS
        SELECT * FROM read_csv_auto('{csv_path}', header=true)
        {limit_clause}
    """)

    row_count = con.execute("SELECT COUNT(*) FROM main_data").fetchone()[0]
    columns = [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name='main_data'"
    ).fetchall()]

    con.close()

    from src.ingest.schema_registry import register_schema
    register_schema(csv_path=csv_path, db_path=db_path)

    return {"rows_loaded": row_count, "columns": columns, "db_path": db_path}


if __name__ == "__main__":
    result = load_csv()
    print(f"Loaded {result['rows_loaded']:,} rows | {len(result['columns'])} columns → {result['db_path']}")
