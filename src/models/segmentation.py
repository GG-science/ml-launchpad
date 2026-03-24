"""
Customer segmentation via KMeans + silhouette scoring.
Reads config, pulls data from DuckDB, clusters, returns SegmentResult.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.ingest.csv_loader import get_connection, DB_PATH, CONFIG_PATH
from src.models.base import SegmentationConfig, SegmentResult

REPORTS_DIR = "outputs/reports"
MODELS_DIR = "outputs/models"


def _load_seg_config(config_path: str = CONFIG_PATH) -> SegmentationConfig:
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    seg = cfg.get("segmentation", {})
    return SegmentationConfig(
        n_clusters=seg.get("n_clusters", "auto"),
        max_clusters=seg.get("max_clusters", 10),
        features=seg.get("features", []),
    )


def _load_data(config: SegmentationConfig, db_path: str = DB_PATH, sample_limit: int = 50_000) -> pd.DataFrame:
    con = get_connection(db_path)
    df = con.execute(f"SELECT * FROM main_data LIMIT {sample_limit}").df()
    con.close()

    # Select numeric features only
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if config.features:
        cols = [c for c in config.features if c in numeric_cols]
    else:
        cols = numeric_cols

    if not cols:
        raise ValueError("No numeric columns found for segmentation.")

    return df[cols].dropna()


def _find_optimal_k(X_scaled, max_k: int) -> int:
    """Elbow method: pick k where inertia improvement drops below 10%."""
    inertias = []
    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    for i in range(1, len(inertias)):
        improvement = (inertias[i - 1] - inertias[i]) / inertias[i - 1]
        if improvement < 0.1:
            return i + 1  # k starts at 2
    return max_k


def run_segmentation(
    db_path: str = DB_PATH,
    config_path: str = CONFIG_PATH,
) -> SegmentResult:
    """Run KMeans segmentation and return SegmentResult."""
    with open(config_path) as f:
        cfg_raw = yaml.safe_load(f)
    sample_limit = cfg_raw["data"].get("sample_row_limit", 50_000)

    config = _load_seg_config(config_path)
    df = _load_data(config, db_path, sample_limit)

    warn_list: list[str] = []

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)

    if config.n_clusters == "auto":
        k = _find_optimal_k(X_scaled, config.max_clusters)
        warn_list.append(f"Optimal k selected automatically: {k} (elbow method, max_k={config.max_clusters})")
    else:
        k = int(config.n_clusters)

    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    sil = round(silhouette_score(X_scaled, labels), 4) if len(set(labels)) > 1 else 0.0

    df = df.copy()
    df["cluster"] = labels
    cluster_sizes = df["cluster"].value_counts().to_dict()
    cluster_profiles = [
        {"cluster": int(c), **df[df["cluster"] == c].drop(columns="cluster").mean().round(4).to_dict()}
        for c in sorted(cluster_sizes.keys())
    ]

    result = SegmentResult(
        n_clusters=k,
        silhouette_score=sil,
        cluster_sizes={int(k): int(v) for k, v in cluster_sizes.items()},
        cluster_profiles=cluster_profiles,
        warnings=warn_list,
    )

    _write_segment_report(result, df.drop(columns="cluster").columns.tolist())

    from src.experiments.tracker import log_segmentation_run
    log_segmentation_run(result, config_path=config_path)

    return result


def _write_segment_report(result: SegmentResult, features: list[str]) -> None:
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    lines = [
        "## Segmentation Results (KMeans)",
        f"**Clusters:** {result.n_clusters}  |  **Silhouette Score:** {result.silhouette_score:.4f}",
        "",
        "### Cluster Sizes",
        "| Cluster | Count | % |",
        "|---------|-------|---|",
    ]
    total = sum(result.cluster_sizes.values())
    for cid, count in sorted(result.cluster_sizes.items()):
        lines.append(f"| {cid} | {count:,} | {count/total*100:.1f}% |")

    lines += ["", "### Cluster Profiles (feature means)", "| Cluster | " + " | ".join(features) + " |"]
    lines.append("|---------|" + "|".join(["------"] * len(features)) + "|")
    for profile in result.cluster_profiles:
        vals = [str(profile.get(f, "—")) for f in features]
        lines.append(f"| {profile['cluster']} | " + " | ".join(vals) + " |")

    if result.warnings:
        lines += ["", "### Notes"]
        lines += [f"- {w}" for w in result.warnings]

    Path(f"{REPORTS_DIR}/model_results.md").write_text("\n".join(lines))
