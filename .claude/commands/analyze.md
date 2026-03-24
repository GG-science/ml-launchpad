Run an ad-hoc analysis on the loaded data. This is the flexible mode for marketing, ads, and business analysis work.

The user will describe what they want to understand. Use DuckDB SQL queries and Python to answer their question.

Common analysis patterns — use these as starting points:
- **Funnel analysis**: conversion rates between stages, drop-off points
- **Cohort analysis**: group by signup/first-purchase date, track retention
- **Channel attribution**: which channels drive conversions, CAC by channel
- **ROAS/ad performance**: spend vs revenue by campaign, diminishing returns
- **RFM analysis**: recency × frequency × monetary scoring
- **Customer lifetime value**: predict or calculate LTV by segment
- **A/B test analysis**: statistical significance, effect size, confidence intervals
- **Trend analysis**: time-series breakdowns, seasonality, week-over-week

How to run:
1. Connect to DuckDB: data/processed/store.duckdb
2. Query main_data with DuckDB SQL (fast, supports window functions, CTEs)
3. Write results to a markdown report in outputs/reports/
4. Summarise findings for the user with actionable takeaways

Always:
- Show the SQL or code you ran so the user can verify
- Include sample sizes — "this insight is based on N rows"
- Flag when sample sizes are too small for reliable conclusions
- Suggest follow-up questions based on what you find
