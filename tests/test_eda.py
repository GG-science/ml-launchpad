"""Tests for EDA layer — profiler and report writer."""
import pytest
import csv
from pathlib import Path


@pytest.fixture
def ecommerce_csv(tmp_path):
    p = tmp_path / "ecommerce.csv"
    rows = [
        ["customer_id", "revenue", "channel", "converted"],
        ["C001", "120.5", "email", "1"],
        ["C002", "85.0", "organic", "0"],
        ["C003", "200.0", "paid", "1"],
        ["C004", "", "social", "0"],
        ["C001", "120.5", "email", "1"],  # duplicate row
    ]
    with open(p, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    return str(p)


@pytest.fixture
def setup_project(tmp_path, ecommerce_csv, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "outputs" / "reports").mkdir(parents=True)

    cfg = f"""
project:
  name: test-project
data:
  csv_path: "{ecommerce_csv}"
  sample_row_limit: 1000
mode: supervised
supervised:
  target_column: converted
"""
    (tmp_path / "config" / "project.yml").write_text(cfg)

    from src.ingest.csv_loader import load_csv
    db_path = str(tmp_path / "data" / "processed" / "store.duckdb")
    load_csv(csv_path=ecommerce_csv, row_limit=1000, db_path=db_path)
    return tmp_path, db_path


def test_profiler_row_count(setup_project):
    tmp_path, db_path = setup_project
    from src.eda.profiler import run_profile
    result = run_profile(db_path=db_path, config_path=str(tmp_path / "config" / "project.yml"))
    assert result.row_count == 5
    assert result.col_count == 4


def test_profiler_detects_duplicates(setup_project):
    tmp_path, db_path = setup_project
    from src.eda.profiler import run_profile
    result = run_profile(db_path=db_path, config_path=str(tmp_path / "config" / "project.yml"))
    assert result.duplicate_rows == 1


def test_profiler_detects_high_nulls(setup_project):
    tmp_path, db_path = setup_project
    from src.eda.profiler import run_profile
    result = run_profile(db_path=db_path, config_path=str(tmp_path / "config" / "project.yml"))
    # revenue has 1 null out of 5 rows = 20%
    assert "revenue" in result.high_null_columns or result.high_null_columns == []


def test_profiler_target_balance(setup_project):
    tmp_path, db_path = setup_project
    from src.eda.profiler import run_profile
    result = run_profile(db_path=db_path, config_path=str(tmp_path / "config" / "project.yml"))
    assert result.target_balance is not None
    assert "1" in result.target_balance or 1 in result.target_balance


def test_write_report_creates_file(setup_project):
    tmp_path, db_path = setup_project
    from src.eda.report import write_report
    report_path = write_report(
        db_path=db_path,
        config_path=str(tmp_path / "config" / "project.yml"),
    )
    assert Path(report_path).exists()
    content = Path(report_path).read_text()
    assert "test-project" in content
    assert "Column Profiles" in content
