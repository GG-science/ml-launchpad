Run deep exploratory data analysis on the loaded dataset.

Steps:
1. Load config from config/project.yml
2. Confirm data is loaded in DuckDB (if not, run the loader first: `uv run python -c "from src.ingest.csv_loader import load_csv; load_csv()"`)
3. Run the profiler: `uv run python -c "from src.eda.profiler import run_profile; run_profile()"`
4. Write the report: `uv run python -c "from src.eda.report import write_report; write_report()"`
5. Read outputs/reports/eda_report.md

Now give the user a thorough briefing:

**Data shape:** rows, columns, types breakdown (numeric/categorical/date)

**Data quality issues:** nulls, duplicates, constant columns, high-cardinality (ID-like) columns

**Distribution insights:** which columns are skewed, where outliers are, quartile spreads

**Top correlations:** strongest feature-feature correlations — flag multicollinearity risks

**Target analysis (if supervised):**
- Class balance
- Which features show the biggest difference between target groups (feature-target means/rates)
- Which categorical values have the highest/lowest positive rates

**Actionable recommendations:** the profiler generates these — read them and expand with your own interpretation. Be specific: "discount_pct has a 42% positive rate vs 28% for full-price — discounts appear to drive conversions"

**If exploration mode:** suggest 5 specific, interesting analytical questions based on what you found. e.g., "Channel attribution: email shows 2x the conversion rate of paid search — worth investigating if this holds after controlling for customer segment"

End with: "Run **/model** to train models, **/analyze** for ad-hoc deep dives, or ask me any question about this data."
