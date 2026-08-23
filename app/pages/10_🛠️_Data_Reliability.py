"""Data Reliability — Admin pipeline health dashboard."""
import streamlit as st
import io
import contextlib

st.set_page_config(page_title="AgriIntel — Data Reliability", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

from app.app_core import init_page
from app.terminal_theme import render_footer, style_dataframe

ctx = init_page()
db_manager = ctx["db_manager"]
last_db_update = ctx["last_db_update"]
user_role = ctx["user_role"]

if user_role not in ["Admin", "Analyst"]:
    st.error("🔒 Admin access required.")
    st.stop()

st.header("🛠️ Data Reliability Dashboard")
st.caption("Monitor the health of the data ingestion pipeline and scraper performance.")

# 1. Scraper Stats
stats_df, success_rate = db_manager.get_scraper_stats()

col1, col2, col3 = st.columns(3)
col1.metric("Scraper Success Rate", f"{success_rate:.1f}%")
if not stats_df.empty:
    avg_time = stats_df['duration_seconds'].mean()
    col2.metric("Avg Execution Time", f"{avg_time:.1f}s")
    last_run = stats_df.iloc[0]['timestamp']
    col3.metric("Last Run", last_run)
else:
    col2.metric("Avg Execution Time", "N/A")
    col3.metric("Last Run", "N/A")

st.subheader("Recent Execution Logs")
st.dataframe(style_dataframe(stats_df), use_container_width=True)

st.markdown("---")

# 2. Quality Alerts
st.subheader("🚨 Data Quality Alerts")
alerts_df = db_manager.get_recent_quality_alerts()

if not alerts_df.empty:
    def highlight_severity(val):
        color = 'red' if val == 'CRITICAL' else 'orange' if val == 'WARNING' else 'black'
        return f'color: {color}'

    st.dataframe(style_dataframe(alerts_df.style.map(highlight_severity, subset=['severity'])), use_container_width=True)
else:
    st.success("✅ No recent data quality issues detected.")

# 3. Manual Trigger
st.markdown("---")
st.subheader("⚙️ Pipeline Control")
if st.button("Run Manual Data Update (Admin)"):
    with st.spinner("Running ETL Pipeline..."):
        f = io.StringIO()
        import etl.data_loader
        with contextlib.redirect_stdout(f):
            etl.data_loader.run_daily_update()

        output = f.getvalue()
        st.code(output)
        st.success("Manual Update Complete!")
        st.rerun()

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
