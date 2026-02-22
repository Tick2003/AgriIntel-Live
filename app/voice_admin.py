import streamlit as st
import pandas as pd
import plotly.express as px
import database.db_manager as db_manager
import json

def show_voice_admin():
    st.title("🎙️ Voice Intelligence Admin Panel")
    st.markdown("Monitor real-time voice interactions and system performance.")

    # 1. Fetch Call Logs
    conn = db_manager.sqlite3.connect(db_manager.DB_NAME)
    try:
        df = pd.read_sql("SELECT * FROM voice_call_logs ORDER BY timestamp DESC", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        st.info("No voice call logs found yet.")
        return

    # 2. Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Calls", len(df))
    with col2:
        st.metric("Unique Callers", df['phone_number'].nunique())
    with col3:
        avg_conf = df['confidence_score'].mean() * 100 if not df.empty else 0
        st.metric("Avg ASR Confidence", f"{avg_conf:.1f}%")
    with col4:
        st.metric("Daily Calls", len(df[df['timestamp'].str.contains(pd.Timestamp.now().strftime("%Y-%m-%d"))]))

    # 3. Charts
    c1, c2 = st.columns(2)
    with c1:
        lang_dist = df['language'].value_counts().reset_index()
        lang_dist.columns = ['Language', 'Count']
        fig = px.pie(lang_dist, values='Count', names='Language', title="Language Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        intent_dist = df['intent'].value_counts().reset_index()
        intent_dist.columns = ['Intent', 'Count']
        fig2 = px.bar(intent_dist, x='Intent', y='Count', title="Intent Classification Accuracy")
        st.plotly_chart(fig2, use_container_width=True)

    # 4. Transcript Logs
    st.subheader("📜 Detailed Call Transcripts")
    
    # Filter by Language
    lang_filter = st.multiselect("Filter by Language", options=df['language'].unique(), default=df['language'].unique())
    filtered_df = df[df['language'].isin(lang_filter)]

    for _, row in filtered_df.head(20).iterrows():
        with st.expander(f"📞 {row['phone_number']} | {row['timestamp']} | {row['language'].upper()}"):
            c_a, c_b = st.columns([1, 2])
            with c_a:
                st.write(f"**Intent:** {row['intent']}")
                st.write(f"**Region:** {row['region']}")
                st.write(f"**Confidence:** {row['confidence_score']:.2f}")
            with c_b:
                st.write(f"**User:** {row['transcript']}")
                st.write(f"**AI:** {row['response_text']}")
                try:
                    entities = json.loads(row['entities'])
                    st.json(entities)
                except:
                    pass

    # 5. Export
    st.download_button(
        label="📥 Export Call Reports (CSV)",
        data=df.to_csv(index=False),
        file_name="voice_call_reports.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    show_voice_admin()
