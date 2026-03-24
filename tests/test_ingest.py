"""Tests for ingest layer — csv_loader and schema_registry."""
import pytest
import tempfile
import csv
import os
from pathlib import Path


@pytest.fixture
def sample_csv(tmp_path):
    p = tmp_path / "test.csv"
    rows = [
        ["customer_id", "revenue", "channel", "converted"],
        ["C001", "120.5", "email", "1"],
        ["C002", "85.0", "organic", "0"],
        ["C003", "200.0", "paid", "1"],
        ["C004", "", "social", "0"],   # null revenue
    ]
    with open(p, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return str(p)


@pytest.fixture
def test_db(tmp_path):
    return str(tmp_path / "test_store.duckdb")


@pytest.fixture
def mock_config(tmp_path, sample_csv, monkeypatch):
    cfg_path = tmp_path / "project.yml"
    cfg_path.write_text(f"""
project:
  name: test-project
data:
  csv_path: "{sample_csv}"
  sample_row_limit: 1000
mode: supervised
supervised:
  target_column: converted
""")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "project.yml").write_text(cfg_path.read_text())
    (tmp_path / "data" / "processed").mkdir(parents=True)
    return str(cfg_path)


def test_load_csv_returns_correct_row_count(sample_csv, test_db, mock_config):
    from src.ingest.csv_loader import load_csv
    result = load_csv(csv_path=sample_csv, row_limit=100, db_path=test_db)
    assert result["rows_loaded"] == 4
    assert "customer_id" in result["columns"]
    assert "converted" in result["columns"]


def test_load_csv_respects_row_limit(sample_csv, test_db, mock_config):
    from src.ingest.csv_loader import load_csv
    result = load_csv(csv_path=sample_csv, row_limit=2, db_path=test_db)
    assert result["rows_loaded"] == 2


def test_load_csv_missing_file_raises(test_db, mock_config):
    from src.ingest.csv_loader import load_csv
    with pytest.raises(FileNotFoundError):
        load_csv(csv_path="/nonexistent/path.csv", db_path=test_db)


def test_schema_registry_populated(sample_csv, test_db, mock_config):
    from src.ingest.csv_loader import load_csv
    from src.ingest.schema_registry import get_schema
    load_csv(csv_path=sample_csv, row_limit=100, db_path=test_db)
    schema = get_schema(db_path=test_db)
    columns = [s["column"] for s in schema]
    assert "customer_id" in columns
    assert "converted" in columns


def test_schema_registry_records_nulls(sample_csv, test_db, mock_config):
    from src.ingest.csv_loader import load_csv
    from src.ingest.schema_registry import get_schema
    load_csv(csv_path=sample_csv, row_limit=100, db_path=test_db)
    schema = get_schema(db_path=test_db)
    revenue_col = next(s for s in schema if s["column"] == "revenue")
    assert revenue_col["null_count"] == 1
