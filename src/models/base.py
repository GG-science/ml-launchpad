"""Shared config and result types for all model layers."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SupervisedConfig:
    target_column: str
    task_type: str = "auto"             # auto | binary | multiclass | regression
    time_limit: int = 120               # seconds
    sample_row_limit: int | None = 50_000
    excluded_columns: list[str] = field(default_factory=list)


@dataclass
class SegmentationConfig:
    n_clusters: int | str = "auto"      # int or "auto" (elbow method)
    max_clusters: int = 10
    features: list[str] = field(default_factory=list)  # empty = all numeric


@dataclass
class ModelEntry:
    name: str
    metric_value: float
    metric_name: str


@dataclass
class SupervisedResult:
    best_model: str
    metric_name: str
    metric_value: float
    leaderboard: list[ModelEntry]
    feature_importance: dict[str, float]   # feature → importance score
    task_type: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class SegmentResult:
    n_clusters: int
    silhouette_score: float
    cluster_sizes: dict[int, int]          # cluster_id → row count
    cluster_profiles: list[dict[str, Any]] # per-cluster feature means
    warnings: list[str] = field(default_factory=list)
