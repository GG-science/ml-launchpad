"""Tests for ML layer — base types, segmentation, and tracker.
AutoGluon tests are skipped if not installed (heavy dependency).
"""
import pytest
import csv
from pathlib import Path


@pytest.fixture
def setup_segmentation_project(tmp_path, monkeypatch):
    """Set up a segmentation project with numeric data."""
    monkeypatch.chdir(tmp_path)

    csv_path = tmp_path / "seg_data.csv"
    import random
    random.seed(42)
    rows = [["revenue", "frequency", "recency", "age"]]
    for _ in range(200):
        rows.append([
            round(random.uniform(10, 500), 2),
            random.randint(1, 50),
            random.randint(0, 365),
            random.randint(18, 80),
        ])
    with open(csv_path, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    (tmp_path / "config").mkdir()
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "outputs" / "reports").mkdir(parents=True)
    (tmp_path / "experiments").mkdir()

    cfg = f"""
project:
  name: test-segmentation
data:
  csv_path: "{csv_path}"
  sample_row_limit: 200
mode: segmentation
segmentation:
  n_clusters: 3
  features: []
mlflow:
  experiment_name: test-seg
  tracking_uri: "{tmp_path}/experiments/mlruns"
"""
    (tmp_path / "config" / "project.yml").write_text(cfg)

    db_path = str(tmp_path / "data" / "processed" / "store.duckdb")
    from src.ingest.csv_loader import load_csv
    load_csv(csv_path=str(csv_path), row_limit=200, db_path=db_path)
    return tmp_path, db_path


def test_segmentation_runs(setup_segmentation_project):
    tmp_path, db_path = setup_segmentation_project
    from src.models.segmentation import run_segmentation
    result = run_segmentation(
        db_path=db_path,
        config_path=str(tmp_path / "config" / "project.yml"),
    )
    assert result.n_clusters == 3
    assert 0 < result.silhouette_score <= 1
    assert sum(result.cluster_sizes.values()) == 200


def test_segmentation_auto_k(setup_segmentation_project):
    tmp_path, db_path = setup_segmentation_project
    cfg_path = tmp_path / "config" / "project.yml"
    import yaml
    cfg = yaml.safe_load(cfg_path.read_text())
    cfg["segmentation"]["n_clusters"] = "auto"
    cfg_path.write_text(yaml.dump(cfg))

    from src.models.segmentation import run_segmentation
    result = run_segmentation(
        db_path=db_path,
        config_path=str(cfg_path),
    )
    assert 2 <= result.n_clusters <= 10


def test_segmentation_writes_report(setup_segmentation_project):
    tmp_path, db_path = setup_segmentation_project
    from src.models.segmentation import run_segmentation
    run_segmentation(
        db_path=db_path,
        config_path=str(tmp_path / "config" / "project.yml"),
    )
    report = tmp_path / "outputs" / "reports" / "model_results.md"
    assert report.exists()
    assert "Segmentation Results" in report.read_text()


def test_mlflow_logs_segmentation(setup_segmentation_project):
    tmp_path, db_path = setup_segmentation_project
    import mlflow
    from src.models.segmentation import run_segmentation
    run_segmentation(
        db_path=db_path,
        config_path=str(tmp_path / "config" / "project.yml"),
    )
    mlflow.set_tracking_uri(str(tmp_path / "experiments" / "mlruns"))
    runs = mlflow.search_runs(experiment_names=["test-seg"])
    assert len(runs) >= 1
    assert "metrics.silhouette_score" in runs.columns


def test_base_types():
    from src.models.base import SupervisedConfig, SegmentationConfig, ModelEntry
    sc = SupervisedConfig(target_column="converted")
    assert sc.time_limit == 120
    seg = SegmentationConfig(n_clusters="auto")
    assert seg.max_clusters == 10
    me = ModelEntry(name="xgb", metric_value=0.85, metric_name="accuracy")
    assert me.metric_value == 0.85
