"""Quality Grading (CV) — Upload images for institutional produce grading."""
import streamlit as st
import os
import tempfile

st.set_page_config(page_title="AgriIntel — Quality Grading", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

from app.app_core import init_page
from app.terminal_theme import render_footer

ctx = init_page()
last_db_update = ctx["last_db_update"]
user_role = ctx["user_role"]

if user_role not in ["Admin", "Analyst"]:
    st.error("🔒 Admin access required.")
    st.stop()

st.markdown("<h1>Structural Quality Analytics</h1>", unsafe_allow_html=True)
st.write("Upload visual data for institutional grading (Grade A/B/C).")

from cv.grading_model import GradingModel
grader = GradingModel()

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    c1, c2 = st.columns(2)
    with c1:
        st.image(uploaded_file, caption="Uploaded Produce", use_container_width=True)

    with c2:
        with st.spinner("Analyzing quality..."):
            # Save temp file for the mock/real grader (unique name for multi-user safety)
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp.write(uploaded_file.getbuffer())
                temp_path = tmp.name

            try:
                result = grader.predict(temp_path)
            finally:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

        if result:
            grade = result['grade']
            color = "green" if grade == "Grade A" else "orange" if grade == "Grade B" else "red"

            st.markdown(f"### Grade: :{color}[{grade}]")
            st.metric("Confidence", f"{result['confidence']*100:.1f}%")
            st.info(f"**Details**: {result['details']}")

            if grade == "Grade A":
                st.success("✨ Premium Quality! You can list this at a 10-15% premium price.")
            elif grade == "Grade C":
                st.warning("⚠️ Low Grade. Recommended for processing/canning industries rather than direct retail.")

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
