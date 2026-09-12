"""News — Intelligence Feed with global agri-sentiment."""
import streamlit as st

st.set_page_config(page_title="AgriIntel — News", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

import os as _os, sys as _sys
_repo_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if _repo_root not in _sys.path:
    _sys.path.insert(0, _repo_root)

from app.app_core import init_page, safe_html
from app.terminal_theme import (
    ACCENT_BLUE,
    ACCENT_GREEN,
    TEXT_SECONDARY,
    render_footer,
)
from app.utils import get_news_feed

ctx = init_page()
last_db_update = ctx["last_db_update"]

st.markdown("<h1>Intelligence Feed: Global Agri-Sentiment</h1>", unsafe_allow_html=True)

news_df = get_news_feed()
if not news_df.empty:
    for index, row in news_df.iterrows():
        st.markdown(f"""
            <div class='terminal-panel'>
                <p style='color:{ACCENT_BLUE}; font-size:0.8rem; margin-bottom:5px;'>{safe_html(row['date'])} | {safe_html(row['source'])}</p>
                <h3 style='margin-top:0;'>{safe_html(row['title'])}</h3>
                <p style='color:{TEXT_SECONDARY};'>{safe_html(row['sentiment'])}</p>
                <a href='{safe_html(row['url'])}' style='color:{ACCENT_GREEN}; text-decoration:none;'>Read Analysis →</a>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("Searching for intelligence signals... (Feed Empty)")

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
