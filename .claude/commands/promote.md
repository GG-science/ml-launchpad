Save the trained model artifact and log to MLflow.

Run: `uv run python -c "from src.experiments.tracker import promote_model; promote_model()"`

Then say: "Model promoted. View all runs: `uv run mlflow ui --backend-store-uri experiments/mlruns`"
