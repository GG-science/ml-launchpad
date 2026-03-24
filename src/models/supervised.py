"""
AutoGluon supervised training wrapper.
Reads config, pulls data from DuckDB, trains, returns SupervisedResult.
MLflow logging is handled by tracker.py — import and call log_supervised_run().
"""
from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd
import yaml

from src.ingest.csv_loader import get_connection, DB_PATH, CONFIG_PATH
from src.models.base import SupervisedConfig, SupervisedResult, ModelEntry

MODELS_DIR = "outputs/models"
REPORTS_DIR = "outputs/reports"


def _load_supervised_config(config_path: str = CONFIG_PATH) -> SupervisedConfig:
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    sup = cfg.get("supervised", {})
    return SupervisedConfig(
        target_column=sup["target_column"],
        task_type=sup.get("task_type", "auto"),
        time_limit=sup.get("time_limit_seconds", 120),
        sample_row_limit=cfg["data"].get("sample_row_limit", 50_000),
    )


def _load_data(config: SupervisedConfig, db_path: str = DB_PATH) -> pd.DataFrame:
    con = get_connection(db_path)
    limit = f"LIMIT {config.sample_row_limit}" if config.sample_row_limit else ""
    df = con.execute(f"SELECT * FROM main_data {limit}").df()
    con.close()
    return df


def run_supervised(
    db_path: str = DB_PATH,
    config_path: str = CONFIG_PATH,
    models_dir: str = MODELS_DIR,
) -> SupervisedResult:
    """Train with AutoGluon on sample data and return SupervisedResult."""
    try:
        from autogluon.tabular import TabularPredictor
    except ImportError:
        raise ImportError("AutoGluon not installed. Run: uv add autogluon")

    config = _load_supervised_config(config_path)
    df = _load_data(config, db_path)

    warn_list: list[str] = []

    if config.target_column not in df.columns:
        raise ValueError(f"Target column '{config.target_column}' not in data. Columns: {list(df.columns)}")

    # Class imbalance check
    if config.task_type in ("auto", "binary", "multiclass"):
        vc = df[config.target_column].value_counts(normalize=True)
        if vc.iloc[-1] < 0.05:
            warn_list.append(f"Class imbalance detected: minority class is {vc.iloc[-1]:.1%} of data.")

    save_path = Path(models_dir) / "autogluon_model"
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        predictor = TabularPredictor(
            label=config.target_column,
            path=str(save_path),
            verbosity=0,
        ).fit(
            train_data=df,
            time_limit=config.time_limit,
            presets="medium_quality",
        )

    lb = predictor.leaderboard(silent=True)
    metric_name = predictor.eval_metric.name if hasattr(predictor.eval_metric, "name") else str(predictor.eval_metric)

    leaderboard = [
        ModelEntry(
            name=str(row["model"]),
            metric_value=float(row["score_val"]),
            metric_name=metric_name,
        )
        for _, row in lb.head(10).iterrows()
    ]

    try:
        fi = predictor.feature_importance(df, silent=True)
        feature_importance = {str(k): float(v) for k, v in fi["importance"].head(10).items()}
    except Exception:
        feature_importance = {}

    result = SupervisedResult(
        best_model=str(lb.iloc[0]["model"]),
        metric_name=metric_name,
        metric_value=float(lb.iloc[0]["score_val"]),
        leaderboard=leaderboard,
        feature_importance=feature_importance,
        task_type=predictor.problem_type,
        warnings=warn_list,
    )

    _write_model_report(result)

    from src.experiments.tracker import log_supervised_run
    log_supervised_run(result, config_path=config_path)

    return result


def _write_model_report(result: SupervisedResult) -> None:
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    lines = [
        "## Model Results (AutoGluon)",
        f"**Task:** {result.task_type}  |  **Metric:** {result.metric_name}",
        "",
        "### Leaderboard",
        "| Rank | Model | Score |",
        "|------|-------|-------|",
    ]
    for i, entry in enumerate(result.leaderboard, 1):
        lines.append(f"| {i} | {entry.name} | {entry.metric_value:.4f} |")

    if result.feature_importance:
        lines += [
            "",
            "### Top Feature Importance",
            "| Feature | Importance |",
            "|---------|------------|",
        ]
        for feat, imp in sorted(result.feature_importance.items(), key=lambda x: -x[1]):
            lines.append(f"| {feat} | {imp:.4f} |")

    if result.warnings:
        lines += ["", "### ⚠️ Warnings"]
        lines += [f"- {w}" for w in result.warnings]

    Path(f"{REPORTS_DIR}/model_results.md").write_text("\n".join(lines))
