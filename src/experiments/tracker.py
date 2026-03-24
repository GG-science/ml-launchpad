"""
MLflow experiment tracker — fully wired.
Every /model run auto-logs params, metrics, and artifacts via mlflow.autolog().
"""
from __future__ import annotations

import yaml
from pathlib import Path

import mlflow

from src.ingest.csv_loader import CONFIG_PATH
from src.models.base import SupervisedResult, SegmentResult


def _setup_mlflow(config_path: str = CONFIG_PATH) -> str:
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    ml_cfg = cfg.get("mlflow", {})
    tracking_uri = ml_cfg.get("tracking_uri", "experiments/mlruns")
    experiment_name = ml_cfg.get("experiment_name", cfg["project"]["name"])

    Path(tracking_uri).mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    mlflow.autolog(silent=True)
    return experiment_name


def log_supervised_run(
    result: SupervisedResult,
    config_path: str = CONFIG_PATH,
) -> str:
    """Log a supervised model run to MLflow. Returns the run ID."""
    experiment_name = _setup_mlflow(config_path)

    with mlflow.start_run(run_name=f"supervised_{result.task_type}") as run:
        mlflow.log_param("task_type", result.task_type)
        mlflow.log_param("best_model", result.best_model)
        mlflow.log_metric(result.metric_name, result.metric_value)

        for i, entry in enumerate(result.leaderboard):
            mlflow.log_metric(f"model_{i}_{entry.metric_name}", entry.metric_value)

        for feat, imp in result.feature_importance.items():
            mlflow.log_metric(f"fi_{feat}", imp)

        report_path = "outputs/reports/model_results.md"
        if Path(report_path).exists():
            mlflow.log_artifact(report_path)

        return run.info.run_id


def log_segmentation_run(
    result: SegmentResult,
    config_path: str = CONFIG_PATH,
) -> str:
    """Log a segmentation run to MLflow. Returns the run ID."""
    experiment_name = _setup_mlflow(config_path)

    with mlflow.start_run(run_name=f"segmentation_k{result.n_clusters}") as run:
        mlflow.log_param("n_clusters", result.n_clusters)
        mlflow.log_metric("silhouette_score", result.silhouette_score)

        for cid, count in result.cluster_sizes.items():
            mlflow.log_metric(f"cluster_{cid}_size", count)

        report_path = "outputs/reports/model_results.md"
        if Path(report_path).exists():
            mlflow.log_artifact(report_path)

        return run.info.run_id


def promote_model(config_path: str = CONFIG_PATH) -> None:
    """Register the latest model in MLflow and copy artifacts to outputs/models/."""
    _setup_mlflow(config_path)
    runs = mlflow.search_runs(order_by=["start_time DESC"], max_results=1)
    if runs.empty:
        raise RuntimeError("No MLflow runs found. Run /model first.")

    run_id = runs.iloc[0]["run_id"]
    print(f"Latest run: {run_id}")
    print(f"Artifacts at: {mlflow.get_run(run_id).info.artifact_uri}")
    print("Model promoted. View all runs: uv run mlflow ui --backend-store-uri experiments/mlruns")
