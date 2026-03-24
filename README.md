# ml-launchpad

**The ML project template built for Claude Code.**
Drop a CSV → EDA → AutoML → client report — in one session.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet.svg)](https://docs.astral.sh/uv/)

---

## What this is

A consulting-ready ML starter kit. You clone it, drop a CSV, and Claude Code walks you through EDA, model training, and a client-ready report — with guardrails that prevent runaway compute.

**Two modes:**
- **Supervised** — predict a target column (churn, conversion, revenue) via AutoGluon (10+ models, auto-tuned)
- **Segmentation** — find customer groups via KMeans + silhouette scoring

**Built-in:**
- DuckDB data layer with schema registry
- MLflow experiment tracking (fully wired — every run auto-logged)
- FastAPI serving endpoint
- Streamlit dashboard
- Docker Compose (API + MLflow UI + dashboard)
- Git worktree support for isolated experiments

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/GG-science/ml-launchpad.git
cd ml-launchpad

# 2. Install
uv sync

# 3. Open Claude Code
claude

# 4. Configure your project
/setup

# 5. Run EDA
/eda

# 6. Train models
/model

# 7. Generate client report
/report
```

That's it. Your report is at `outputs/reports/client_report.md`.

---

## Commands

| Command | What it does |
|---------|-------------|
| `/setup` | Configure project: name, CSV path, mode, target column |
| `/eda` | Profile data on a sample → `outputs/reports/eda_report.md` |
| `/model` | Train AutoGluon (supervised) or KMeans (segmentation) on sample |
| `/fullrun` | Train on full dataset (requires explicit confirmation) |
| `/report` | Generate client-ready markdown summary |
| `/promote` | Save model artifact + log to MLflow |
| `/dashboard` | Launch Streamlit dashboard |
| `/experiment [name]` | Create isolated git worktree for experiments |

---

## What makes this different

Most ML templates give you a folder structure. This one gives you a **Claude co-pilot**.

The `CLAUDE.md` file contains structured instructions that make Claude Code an active partner in your ML workflow — not just a code generator. Claude knows:

- What commands are available and what they do
- To always run on a sample first (configurable row limit)
- To never touch raw data
- To write reports in consulting-friendly format
- To log every run to MLflow automatically

The `.claude/agents/` directory has specialized subagents for EDA and model training that can run in parallel via git worktrees.

---

## Project structure

```
ml-launchpad/
  .claude/
    CLAUDE.md              ← Claude's operating instructions
    settings.json          ← conservative permission defaults
    agents/                ← EDA + model subagents
  .mcp.json                ← pre-configured MCP servers
  config/
    project.yml.example    ← copy this → /setup writes project.yml
  src/
    ingest/                ← CSV → DuckDB + schema registry
    eda/                   ← profiler + report writer
    models/                ← AutoGluon + KMeans
    experiments/           ← MLflow tracker (fully wired)
    serving/               ← FastAPI (/health, /score)
    dashboard/             ← Streamlit (3 tabs)
  docker/                  ← Dockerfile + docker-compose.yml
  data/
    raw/                   ← your CSVs (gitignored)
    sample/                ← example e-commerce dataset
  outputs/
    reports/               ← generated reports (committed)
    models/                ← model artifacts (gitignored)
  tests/                   ← pytest suite
```

---

## Use cases

- **Customer segmentation** — RFM analysis, behavioral clustering
- **Ads performance** — conversion prediction, ROAS modeling
- **Churn prediction** — identify at-risk customers
- **Personalization** — product recommendation scoring
- **Client reporting** — automated EDA + model summaries

---

## Safety defaults

This template is opinionated about not wasting your compute:

- **Sample-first**: all operations use `sample_row_limit` rows (default: 50,000)
- **Explicit full runs**: `/fullrun` requires typing "yes"
- **Docker memory caps**: API (4GB), MLflow (1GB), Dashboard (2GB)
- **Conservative permissions**: only pre-approved commands run without confirmation
- **No raw data mutation**: `data/raw/` is read-only by convention

---

## Production path

```
/model          → train on sample, validate
/fullrun        → train on full data
/promote        → save artifact + log to MLflow
docker compose up  → API + MLflow + dashboard running
```

Score new data:
```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"features": {"revenue": 120.5, "channel": "email", "frequency": 15}}'
```

---

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Launch dashboard locally
uv run streamlit run src/dashboard/app.py

# Launch MLflow UI
uv run mlflow ui --backend-store-uri experiments/mlruns

# Start all services via Docker
cd docker && docker compose up
```

---

## License

MIT

---

Built with [Claude Code](https://claude.ai/claude-code) + [AutoGluon](https://auto.gluon.ai/) + [DuckDB](https://duckdb.org/) + [MLflow](https://mlflow.org/)
