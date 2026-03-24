"""
Streamlit dashboard — 3 tabs: Data Overview, Model Performance, Segments.
Run: uv run streamlit run src/dashboard/app.py
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="ml-launchpad", layout="wide")
st.title("ml-launchpad Dashboard")


# ---------- Tab setup ----------
tab_data, tab_model, tab_segments = st.tabs(["Data Overview", "Model Performance", "Segments"])


# ---------- Tab 1: Data Overview ----------
with tab_data:
    st.header("Data Overview")

    eda_path = Path("outputs/reports/eda_report.md")
    if eda_path.exists():
        st.markdown(eda_path.read_text())
    else:
        st.info("No EDA report found. Run **/eda** in Claude Code to generate one.")

    # Interactive data explorer
    try:
        import duckdb
        con = duckdb.connect("data/processed/store.duckdb", read_only=True)
        row_count = con.execute("SELECT COUNT(*) FROM main_data").fetchone()[0]
        st.metric("Total Rows", f"{row_count:,}")

        st.subheader("Sample Data")
        sample = con.execute("SELECT * FROM main_data LIMIT 100").df()
        st.dataframe(sample, use_container_width=True)

        st.subheader("Column Stats")
        stats = con.execute("""
            SELECT column_name, data_type, null_count, sample_values
            FROM schema_registry ORDER BY column_name
        """).df()
        st.dataframe(stats, use_container_width=True)
        con.close()
    except Exception as e:
        st.warning(f"Could not load data: {e}. Run **/eda** first.")


# ---------- Tab 2: Model Performance ----------
with tab_model:
    st.header("Model Performance")

    model_path = Path("outputs/reports/model_results.md")
    if model_path.exists():
        st.markdown(model_path.read_text())
    else:
        st.info("No model results found. Run **/model** in Claude Code to train models.")

    # MLflow link
    st.markdown("---")
    st.markdown("View detailed experiment tracking: [MLflow UI](http://localhost:5000)")


# ---------- Tab 3: Segments ----------
with tab_segments:
    st.header("Customer Segments")

    model_path = Path("outputs/reports/model_results.md")
    if model_path.exists() and "Segmentation" in model_path.read_text():
        st.markdown(model_path.read_text())

        try:
            import duckdb
            con = duckdb.connect("data/processed/store.duckdb", read_only=True)
            tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
            if "segment_assignments" in tables:
                segments = con.execute("SELECT * FROM segment_assignments LIMIT 500").df()
                st.subheader("Segment Assignments")
                st.dataframe(segments, use_container_width=True)
            con.close()
        except Exception:
            pass
    else:
        st.info("No segmentation results found. Set mode to **segmentation** and run **/model**.")
