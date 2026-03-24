First-time project configuration. Ask the user these questions in order:

1. "What is this project called?" → project.name
2. "Where is your CSV file?" (default: data/raw/) → data.csv_path
3. "What kind of analysis?"
   - **supervised** — predict a target column (churn, conversion, revenue, clicks)
   - **segmentation** — find customer groups (RFM, behavioral clusters)
   - **exploration** — open-ended analysis, marketing reporting, funnel analysis, ad-hoc questions
4. If supervised: "Which column are you trying to predict?" → supervised.target_column
5. "Sample row limit for fast runs? (default: 50000)" → data.sample_row_limit

Then:
- Copy config/project.yml.example to config/project.yml
- Fill in the user's answers
- Run the CSV loader: `uv run python -c "from src.ingest.csv_loader import load_csv; load_csv()"`
- Say: "Config saved and data loaded. Run **/eda** to profile your data."
