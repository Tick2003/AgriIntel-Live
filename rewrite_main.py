import os

def rewrite_main():
    path = "app/main.py"
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 1. Find the split point (start of Data Reliability page)
    # We look for the user comment I added earlier or the garbled header
    split_idx = -1
    for i, line in enumerate(lines):
        if 'elif page == "Data Reliability":' in line:
            split_idx = i
            break
            
    if split_idx == -1:
        print("Could not find 'Data Reliability' section to replace. Appending instead.")
        # Find end of file? No, just append.
        new_lines = lines + ["\n"]
    else:
        print(f"Found existing section at line {split_idx+1}. Truncating and replacing.")
        new_lines = lines[:split_idx]

    # 2. Append Clean Code
    clean_code = """# --- PAGE: DATA RELIABILITY (New Phase 6) ---
elif page == "Data Reliability":
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
    st.dataframe(stats_df, use_container_width=True)
    
    st.markdown("---")
    
    # 2. Quality Alerts
    st.subheader("🚨 Data Quality Alerts")
    alerts_df = db_manager.get_recent_quality_alerts()
    
    if not alerts_df.empty:
        # Color code severity
        def highlight_severity(val):
            color = 'red' if val == 'CRITICAL' else 'orange' if val == 'WARNING' else 'black'
            return f'color: {color}'
            
        st.dataframe(alerts_df.style.applymap(highlight_severity, subset=['severity']), use_container_width=True)
    else:
        st.success("✅ No recent data quality issues detected.")
    
    # 3. Manual Trigger
    st.markdown("---")
    st.subheader("⚙️ Pipeline Control")
    if st.button("Run Manual Data Update (Admin)"):
        with st.spinner("Running ETL Pipeline..."):
            import contextlib
            import io
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                etl.data_loader.run_daily_update()
            
            output = f.getvalue()
            st.code(output)
            st.success("Manual Update Complete!")
            st.rerun()
"""
    
    final_content = "".join(new_lines) + clean_code
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print("Successfully rewrote app/main.py")

if __name__ == "__main__":
    rewrite_main()
