# ml-launchpad — Claude Co-pilot

## What this is
An ML and data science consulting starter. Drop a CSV, run commands, get EDA + models + analysis + client-ready reports.

Supports three modes:
- **supervised** — predict a target column (churn, conversion, revenue, ad clicks)
- **segmentation** — find customer groups (RFM, behavioral clusters)
- **exploration** — open-ended analysis: marketing reporting, funnel analysis, ROAS, attribution, cohorts, ad-hoc questions

## First time in this repo?
Check if `config/project.yml` exists. If not, tell the user:
> "Run **/setup** to configure this project before anything else."

---

## Available commands

All commands are in `.claude/commands/`. Here's what they do:

| Command | What it does |
|---------|-------------|
| `/setup` | First-time config: name, CSV path, mode, target column |
| `/eda` | Profile data → summary stats, quality issues, patterns |
| `/model` | Train AutoGluon (supervised) or KMeans (segmentation) on sample |
| `/fullrun` | Train on full dataset (requires explicit "yes") |
| `/analyze` | Ad-hoc analysis: funnels, cohorts, ROAS, attribution, any question |
| `/report` | Generate client-ready markdown summary |
| `/promote` | Save model + log to MLflow |
| `/dashboard` | Launch Streamlit dashboard |
| `/experiment [name]` | Create isolated git worktree |

---

## Working with data

**DuckDB is the data layer.** All data lives in `data/processed/store.duckdb`. Query it freely:

```python
import duckdb
con = duckdb.connect("data/processed/store.duckdb")
con.execute("SELECT * FROM main_data LIMIT 10").df()
```

**Schema registry** — after `/setup`, column metadata is stored in the `schema_registry` table. Use it to understand what's available:

```sql
SELECT column_name, dtype, null_count, sample_values FROM schema_registry
```

**For exploration mode** — you're not limited to the pipeline. Use DuckDB SQL directly to answer any question about the data. Common patterns:
- Funnel: conversion rates between stages
- Cohort: group by first-purchase month, track retention
- ROAS: spend vs revenue by channel/campaign
- RFM: recency × frequency × monetary scoring
- Attribution: channel contribution to conversions
- A/B testing: significance tests, confidence intervals

---

## Project structure
```
data/raw/        ← drop CSVs here (gitignored)
data/sample/     ← example e-commerce dataset
src/ingest/      ← CSV → DuckDB + schema registry
src/eda/         ← profiler + markdown report writer
src/models/      ← AutoGluon (supervised) + KMeans (segmentation)
src/experiments/ ← MLflow tracking (fully wired)
src/serving/     ← FastAPI (/health, /score)
src/dashboard/   ← Streamlit (3 tabs)
outputs/reports/ ← generated reports (committed)
outputs/models/  ← model artifacts (gitignored)
experiments/     ← MLflow runs + git worktrees
```

## Key rules
- **Never run on full data without /fullrun confirmation**
- **Never touch data/raw/ files** — read only
- **Always sample first** — default is `sample_row_limit` rows
- **config/project.yml is the source of truth** — read it before every command
- Tests: `uv run pytest tests/ -v`
