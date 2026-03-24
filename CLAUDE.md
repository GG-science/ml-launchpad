# ml-launchpad — Claude Co-pilot

## What this is
An AutoML consulting starter. You drop a CSV, run commands, get EDA + models + a client-ready report.

## First time in this repo?
Check if `config/project.yml` exists. If not, tell the user:
> "Run **/setup** to configure this project before anything else."

---

## Commands

### /setup
**First-time project configuration.**

Ask the user these questions in order:
1. "What is this project called?" → `project.name`
2. "Where is your CSV file?" (default: `data/raw/`) → `data.csv_path`
3. "What mode? Type **supervised** (predict a target column) or **segmentation** (find customer groups)"
4. If supervised: "Which column are you trying to predict?" → `supervised.target_column`
5. "Sample row limit for fast runs? (default: 50000)" → `data.sample_row_limit`

Then:
- Copy `config/project.yml.example` to `config/project.yml`
- Fill in the user's answers
- Say: "Config saved. Run **/eda** to profile your data."

---

### /eda [optional: path/to/file.csv]
**Run exploratory data analysis on a sample.**

Steps:
1. Load config from `config/project.yml`
2. Load up to `sample_row_limit` rows from the CSV into DuckDB: `uv run python -c "from src.ingest.csv_loader import load_csv; load_csv()"`
3. Run the profiler: `uv run python -c "from src.eda.profiler import run_profile; run_profile()"`
4. Write the report: `uv run python -c "from src.eda.report import write_report; write_report()"`
5. Tell the user: "EDA complete → outputs/reports/eda_report.md"
6. Read the report and summarise: top 3 data quality issues, top 3 interesting patterns, recommendation for next step.

---

### /model
**Run AutoGluon (supervised) or KMeans (segmentation) on the sample.**

Steps:
1. Confirm config exists and data is loaded (if not, run /eda first)
2. Show the user: "Running on sample ({sample_row_limit} rows). Time limit: {time_limit_seconds}s."
3. Run: `uv run python -c "from src.models.supervised import run_supervised; run_supervised()"` OR `uv run python -c "from src.models.segmentation import run_segmentation; run_segmentation()"`
4. Read `outputs/reports/model_results.md` and summarise: best model, top 5 features, key metric.
5. Say: "Sample run complete. Run **/fullrun** to train on all data, or **/report** to generate the client summary."

---

### /fullrun
**Train on the full dataset. Requires explicit confirmation.**

Say: "This will run on ALL rows (no sample limit). Type **yes** to confirm."
Wait for "yes". If anything else, abort.

Then run with full data:
- Set `sample_row_limit` to None for this run only
- Same pipeline as /model but with `full_run_time_limit_seconds`

---

### /report
**Generate a client-ready markdown summary.**

Run: `uv run python -c "from src.eda.report import write_client_report; write_client_report()"`

Output: `outputs/reports/client_report.md`

The report should include:
- Dataset overview (rows, columns, date range)
- Top data quality findings
- Model performance (best model, key metric, vs baseline)
- Top 5 predictive features with plain-English interpretation
- Recommended next steps (2–3 bullet points)

---

### /promote
**Save model artifact and log to MLflow.**

Run: `uv run python -c "from src.experiments.tracker import promote_model; promote_model()"`

Saves to `outputs/models/` and logs the run to MLflow.
Say: "Model promoted. View all runs: `uv run mlflow ui --backend-store-uri experiments/mlruns`"

---

### /dashboard
**Launch the Streamlit dashboard.**

Run: `uv run streamlit run src/dashboard/app.py`

---

### /experiment [name]
**Create an isolated git worktree for a new experiment.**

Run:
```
git worktree add experiments/[name] -b experiment/[name]
```
Say: "Worktree created at experiments/[name] on branch experiment/[name]. Work there, then merge what you like back to main."

---

## Project structure
```
data/raw/        ← drop CSVs here
data/sample/     ← example dataset (ecommerce.csv)
src/ingest/      ← CSV → DuckDB
src/eda/         ← profiler + report writer
src/models/      ← AutoGluon + clustering
src/experiments/ ← MLflow tracking
src/serving/     ← FastAPI (productionalize)
src/dashboard/   ← Streamlit (visualise)
outputs/reports/ ← generated reports (committed)
outputs/models/  ← model artifacts (gitignored)
experiments/     ← MLflow runs + worktrees
```

## Key rules
- **Never run on full data without /fullrun confirmation**
- **Never touch data/raw/ files** — read only
- **Always sample first** — default is `sample_row_limit` rows
- **config/project.yml is the source of truth** — read it before every command
- Tests: `uv run pytest tests/ -v`
- Run pipeline stages directly: `uv run python -m src.ingest.csv_loader`
