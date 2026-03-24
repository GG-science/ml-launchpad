Train on the full dataset. This removes the sample row limit.

IMPORTANT: Say "This will run on ALL rows (no sample limit). Type **yes** to confirm."
Wait for the user to type "yes". If anything else, abort.

Then run the same pipeline as /model but with sample_row_limit set to None and using full_run_time_limit_seconds from config.
