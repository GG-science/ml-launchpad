Run exploratory data analysis on the loaded dataset.

Steps:
1. Load config from config/project.yml
2. Confirm data is loaded in DuckDB (if not, run the loader first: `uv run python -c "from src.ingest.csv_loader import load_csv; load_csv()"`)
3. Run the profiler: `uv run python -c "from src.eda.profiler import run_profile; run_profile()"`
4. Write the report: `uv run python -c "from src.eda.report import write_report; write_report()"`
5. Read outputs/reports/eda_report.md
6. Summarise for the user:
   - Dataset shape (rows × columns)
   - Top 3 data quality issues (nulls, duplicates, type mismatches)
   - Top 3 interesting patterns or correlations
   - If supervised mode: target column distribution and balance
   - If segmentation mode: which numeric features are available for clustering
   - If exploration mode: suggest 3-5 interesting questions to explore based on the data
7. Say: "Run **/model** to train models, or ask me any question about this data."
