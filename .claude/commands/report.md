Generate a client-ready markdown summary.

Run: `uv run python -c "from src.eda.report import write_client_report; write_client_report()"`

Then read outputs/reports/client_report.md and enhance it:
- Add an executive summary paragraph in plain English (no jargon)
- Interpret the top features: what do they mean for the business?
- If segmentation: name each segment with a human-readable label (e.g., "High-Value Loyalists", "At-Risk Browsers")
- Add 3 actionable recommendations based on the findings
- Format for a non-technical stakeholder

Save the enhanced report back to outputs/reports/client_report.md.
