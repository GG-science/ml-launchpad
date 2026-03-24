Run model training on the sample dataset.

Steps:
1. Read config/project.yml — check the mode
2. Show the user: "Running on sample ({sample_row_limit} rows). Time limit: {time_limit_seconds}s."

**If supervised:**
- Run: `uv run python -c "from src.models.supervised import run_supervised; run_supervised()"`
- Read outputs/reports/model_results.md
- Summarise: best model, top 5 features, key metric, any warnings

**If segmentation:**
- Run: `uv run python -c "from src.models.segmentation import run_segmentation; run_segmentation()"`
- Read outputs/reports/model_results.md
- Summarise: number of clusters, silhouette score, cluster profiles

**If exploration:**
- Ask the user: "What would you like to model or predict? I can:
  1. Run a quick classification/regression on any column
  2. Cluster the data to find natural groups
  3. Build a custom analysis (funnel, cohort, attribution, etc.)"
- Then run the appropriate model or write a custom analysis script

3. Say: "Sample run complete. Run **/fullrun** to train on all data, or **/report** for the client summary."
