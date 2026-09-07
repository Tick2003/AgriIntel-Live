"""Real-Time Trading Desk — Live order book, transaction feed, intraday charts."""
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="AgriIntel — Real-Time Desk", layout="wide", page_icon="📉", initial_sidebar_state="expanded")

from app.app_core import init_page, safe_html

ctx = init_page()
data = ctx["data"]
forecast_df = ctx["forecast_df"]
risk_info = ctx["risk_info"]
shock_info = ctx["shock_info"]
agents = ctx["agents"]
selected_commodity = ctx["selected_commodity"]
selected_mandi = ctx["selected_mandi"]
last_db_update = ctx["last_db_update"]

from app.terminal_theme import (
    ACCENT_AMBER,
    ACCENT_BLUE,
    ACCENT_GREEN,
    ACCENT_RED,
    BORDER_COLOR,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    get_status_color,
    render_footer,
    render_spacer,
)
from app.utils import get_intraday_data, get_intraday_price_series, get_order_book_data

st.markdown("<h1>Real-Time Trading Desk</h1>", unsafe_allow_html=True)

# --- Start the background stream generator (singleton) ---
if 'stream_started' not in st.session_state:
    try:
        from etl.realtime_stream import start_realtime_generator
        start_realtime_generator(selected_commodity, selected_mandi)
        st.session_state['stream_started'] = True
    except Exception as e:
        st.warning(f"Stream generator unavailable: {e}")

# --- Status Bar ---
status_col1, status_col2, status_col3, status_col4 = st.columns(4)
with status_col1:
    st.markdown(f"""
        <div style='display:flex; align-items:center; gap:8px;'>
            <div style='width:10px; height:10px; border-radius:50%;
                 background-color:{ACCENT_GREEN};
                 box-shadow: 0 0 8px {ACCENT_GREEN};
                 animation: pulse 2s infinite;'></div>
            <span style='color:{ACCENT_GREEN}; font-weight:600; font-size:14px;'>● LIVE</span>
        </div>
        <style>
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.4; }}
            }}
        </style>
    """, unsafe_allow_html=True)
with status_col2:
    st.caption(f"📍 {selected_commodity} | {selected_mandi}")
with status_col3:
    st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
with status_col4:
    if not data.empty:
        st.metric("Daily Modal", f"₹{data['price'].iloc[-1]:,.0f}")

st.markdown(render_spacer("md"), unsafe_allow_html=True)

# --- Row 1: Order Book + Transaction Feed ---
col_book, col_feed = st.columns(2)

with col_book:
    st.subheader("📊 Live Order Book")

    @st.fragment(run_every=3)
    def render_order_book():
        try:
            book = get_order_book_data(selected_commodity, selected_mandi, depth=8)
        except Exception:
            book = {"bids": pd.DataFrame(), "asks": pd.DataFrame()}
        bids = book.get("bids", pd.DataFrame())
        asks = book.get("asks", pd.DataFrame())

        if not bids.empty or not asks.empty:
            bc1, bc2 = st.columns(2)
            with bc1:
                st.markdown(f"<p style='color:{ACCENT_GREEN}; font-weight:700; margin-bottom:4px;'>BID (Buy)</p>", unsafe_allow_html=True)
                if not bids.empty:
                    for _, row in bids.head(8).iterrows():
                        pct_fill = min(100, row['quantity'] / 50 * 100)
                        st.markdown(f"""
                            <div style='position:relative; padding:4px 8px; margin:2px 0; border-radius:4px; overflow:hidden;'>
                                <div style='position:absolute; left:0; top:0; bottom:0; width:{pct_fill}%;
                                     background:rgba(16,185,129,0.15); border-radius:4px;'></div>
                                <div style='position:relative; display:flex; justify-content:space-between;'>
                                    <span style='color:{ACCENT_GREEN}; font-weight:600;'>₹{row['price']:,.0f}</span>
                                    <span style='color:{TEXT_MUTED}; font-size:12px;'>{row['quantity']:.1f}q</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No bids yet...")

            with bc2:
                st.markdown(f"<p style='color:{ACCENT_RED}; font-weight:700; margin-bottom:4px;'>ASK (Sell)</p>", unsafe_allow_html=True)
                if not asks.empty:
                    for _, row in asks.head(8).iterrows():
                        pct_fill = min(100, row['quantity'] / 50 * 100)
                        st.markdown(f"""
                            <div style='position:relative; padding:4px 8px; margin:2px 0; border-radius:4px; overflow:hidden;'>
                                <div style='position:absolute; right:0; top:0; bottom:0; width:{pct_fill}%;
                                     background:rgba(239,68,68,0.15); border-radius:4px;'></div>
                                <div style='position:relative; display:flex; justify-content:space-between;'>
                                    <span style='color:{TEXT_MUTED}; font-size:12px;'>{row['quantity']:.1f}q</span>
                                    <span style='color:{ACCENT_RED}; font-weight:600;'>₹{row['price']:,.0f}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No asks yet...")

            # Spread indicator
            if not bids.empty and not asks.empty:
                spread = asks['price'].iloc[0] - bids['price'].iloc[0]
                st.markdown(f"<p style='text-align:center; color:{ACCENT_BLUE}; font-size:12px; margin-top:8px;'>Spread: ₹{spread:,.0f}</p>", unsafe_allow_html=True)
        else:
            st.info("Order book loading... Stream is initialising.")

    render_order_book()

with col_feed:
    st.subheader("⚡ Live Transaction Feed")

    @st.fragment(run_every=3)
    def render_trade_feed():
        try:
            trades_df = get_intraday_data(selected_commodity, selected_mandi, limit=15)
        except Exception:
            trades_df = pd.DataFrame()
        if not trades_df.empty:
            for _, row in trades_df.iterrows():
                t_type = row.get('trade_type', 'TRADE')
                if t_type == 'BID':
                    icon = "🟢"
                    color = ACCENT_GREEN
                elif t_type == 'ASK':
                    icon = "🔴"
                    color = ACCENT_RED
                else:
                    icon = "⚪"
                    color = ACCENT_BLUE

                ts = str(row.get('timestamp', ''))[-12:]
                st.markdown(f"""
                    <div style='display:flex; justify-content:space-between; align-items:center;
                         padding:4px 8px; border-bottom:1px solid {BORDER_COLOR};'>
                        <span style='font-size:12px;'>{icon} <b style='color:{color};'>{t_type}</b></span>
                        <span style='color:{TEXT_PRIMARY}; font-weight:600;'>₹{row['price']:,.0f}</span>
                        <span style='color:{TEXT_MUTED}; font-size:11px;'>{row['quantity']:.1f}q</span>
                        <span style='color:{TEXT_MUTED}; font-size:10px;'>{ts}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Waiting for transactions... Stream is populating.")

    render_trade_feed()

st.markdown("---")

# --- Row 2: Intraday Chart + RACE Model Card ---
col_chart, col_card = st.columns([3, 1])

with col_chart:
    st.subheader("📈 Intraday Price Chart")

    @st.fragment(run_every=5)
    def render_intraday_chart():
        try:
            intraday_df = get_intraday_price_series(selected_commodity, selected_mandi, limit=80)
        except Exception:
            intraday_df = pd.DataFrame()

        fig = go.Figure()

        if not data.empty:
            fig.add_trace(go.Scatter(
                x=data['date'].iloc[-30:], y=data['price'].iloc[-30:],
                mode='lines', name='Daily Historical',
                line=dict(color=TEXT_MUTED, width=1.5),
                opacity=0.6,
            ))

        if not forecast_df.empty:
            fig.add_trace(go.Scatter(
                x=forecast_df['date'], y=forecast_df['forecast_price'],
                mode='lines', name='RACE Forecast',
                line=dict(color=ACCENT_BLUE, width=2, dash='dot'),
            ))

        if not intraday_df.empty:
            fig.add_trace(go.Scatter(
                x=intraday_df['timestamp'], y=intraday_df['price'],
                mode='lines+markers', name='Intraday Ticks',
                line=dict(color=ACCENT_GREEN, width=2),
                marker=dict(size=4, color=ACCENT_GREEN),
            ))

        fig.update_layout(
            template="agriintel_terminal",
            height=380,
            showlegend=True,
            xaxis_title="Time",
            yaxis_title="Price (₹/Quintal)",
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key="intraday_price_plotly_chart")

    render_intraday_chart()

with col_card:
    st.subheader("🧠 RACE Model Card")

    try:
        from agents.forecast_execution import ForecastingAgent
        forecast_agent = agents.get("forecast") or ForecastingAgent()
        race_result = forecast_agent.get_race_metadata(data, selected_commodity, selected_mandi)
    except Exception:
        race_result = None

    if race_result and not race_result.get("metadata", {}).get("fallback", False):
        regime = race_result.get("regime", "STABLE")
        regime_conf = race_result.get("regime_confidence", 0.5)
        regime_colors = {"STABLE": ACCENT_GREEN, "VOLATILE": ACCENT_AMBER, "CRISIS": ACCENT_RED}
        r_color = regime_colors.get(regime, ACCENT_BLUE)
        st.markdown(f"""
            <div style='background:rgba(255,255,255,0.03); border:1px solid {r_color};
                 border-radius:8px; padding:12px; margin-bottom:12px; text-align:center;'>
                <p style='color:{TEXT_MUTED}; font-size:11px; margin:0; text-transform:uppercase; letter-spacing:0.1em;'>Market Regime</p>
                <p style='color:{r_color}; font-size:24px; font-weight:700; margin:4px 0;'>{regime}</p>
                <p style='color:{TEXT_MUTED}; font-size:11px; margin:0;'>Confidence: {regime_conf:.0%}</p>
            </div>
        """, unsafe_allow_html=True)

        model_weights = race_result.get("model_weights", {})
        st.markdown(f"<p style='color:{TEXT_MUTED}; font-size:11px; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;'>Ensemble Weights</p>", unsafe_allow_html=True)
        for model_name, weight in model_weights.items():
            pct = weight * 100
            bar_color = ACCENT_BLUE if weight > 0.25 else TEXT_MUTED
            st.markdown(f"""
                <div style='margin-bottom:6px;'>
                    <div style='display:flex; justify-content:space-between; font-size:12px;'>
                        <span style='color:{TEXT_SECONDARY};'>{model_name}</span>
                        <span style='color:{TEXT_PRIMARY}; font-weight:600;'>{pct:.1f}%</span>
                    </div>
                    <div style='background:rgba(255,255,255,0.05); border-radius:4px; height:6px; overflow:hidden;'>
                        <div style='background:{bar_color}; width:{pct}%; height:100%; border-radius:4px;
                             transition: width 0.5s ease;'></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        conf_score = race_result.get("confidence", 0.5) * 100
        st.metric("Overall Confidence", f"{conf_score:.0f}/100")
    else:
        st.info("RACE model card loads after forecast execution.")
        st.caption("Run a forecast to populate model metadata.")

st.markdown("---")

# --- Row 3: News Ticker + Shock Alerts ---
col_news, col_alerts = st.columns(2)

with col_news:
    st.subheader("📰 Live News Ticker")
    from app.utils import get_news_feed

    @st.fragment(run_every=30)
    def render_news_ticker():
        news = get_news_feed()
        if not news.empty:
            for _, row in news.head(5).iterrows():
                sent = row.get('sentiment', 'Neutral')
                sent_color = ACCENT_GREEN if sent == 'Positive' else ACCENT_RED if sent == 'Negative' else TEXT_MUTED
                st.markdown(f"""
                    <div style='padding:8px 12px; border-left:3px solid {sent_color};
                         margin-bottom:8px; background:rgba(255,255,255,0.02); border-radius:0 8px 8px 0;'>
                        <p style='color:{TEXT_PRIMARY}; font-size:13px; margin:0 0 4px 0; font-weight:500;'>{safe_html(row['title'])}</p>
                        <div style='display:flex; gap:12px;'>
                            <span style='color:{sent_color}; font-size:11px; font-weight:600;'>{safe_html(sent)}</span>
                            <span style='color:{TEXT_MUTED}; font-size:11px;'>{safe_html(row.get('source', ''))}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("News feed loading...")

    render_news_ticker()

with col_alerts:
    st.subheader("🚨 Real-Time Alerts")

    @st.fragment(run_every=5)
    def render_realtime_alerts():
        try:
            recent_ticks = get_intraday_data(selected_commodity, selected_mandi, limit=100)
            daily_modal_price = data['price'].iloc[-1] if not data.empty else 0.0
            rt_shock = agents["shock"].detect_intraday_shocks(recent_ticks, daily_modal_price)
            rt_risk = agents["risk"].calculate_realtime_risk(risk_info, rt_shock)
        except Exception:
            rt_shock = {"is_shock": False, "severity": "None", "shocks": [], "max_deviation_pct": 0}
            rt_risk = {"risk_score": risk_info.get("risk_score", 0), "risk_level": risk_info.get("risk_level", "Low"), "regime": risk_info.get("regime", "N/A")}

        if rt_shock.get('is_shock', False):
            severity = rt_shock.get('severity', 'Unknown')
            sev_color = ACCENT_RED if severity in ['High', 'Critical'] else ACCENT_AMBER
            st.markdown(f"""
                <div style='background:rgba(239,68,68,0.1); border:1px solid {sev_color};
                     border-radius:8px; padding:16px; margin-bottom:12px;
                     animation: alertPulse 2s infinite;'>
                    <p style='color:{sev_color}; font-size:16px; font-weight:700; margin:0;'>
                        ⚠️ SHOCK DETECTED — {severity}
                    </p>
                    <p style='color:{TEXT_SECONDARY}; font-size:13px; margin:4px 0 0 0;'>
                        Deviation of {rt_shock.get('max_deviation_pct', 0.0)}% from daily modal price. Last shock tick: ₹{rt_shock['shocks'][-1]['price'] if rt_shock['shocks'] else 0:,.2f}
                    </p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='background:rgba(16,185,129,0.05); border:1px solid rgba(16,185,129,0.3);
                     border-radius:8px; padding:16px; margin-bottom:12px;'>
                    <p style='color:{ACCENT_GREEN}; font-size:14px; font-weight:600; margin:0;'>
                        ✅ All Systems Normal
                    </p>
                    <p style='color:{TEXT_MUTED}; font-size:12px; margin:4px 0 0 0;'>
                        No price shocks or anomalies detected.
                    </p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
            <div style='background:rgba(255,255,255,0.02); border:1px solid {BORDER_COLOR};
                 border-radius:8px; padding:12px; margin-top:8px;'>
                <p style='color:{TEXT_MUTED}; font-size:11px; text-transform:uppercase; letter-spacing:0.1em; margin:0 0 8px 0;'>Risk Summary</p>
                <div style='display:flex; justify-content:space-between;'>
                    <div>
                        <p style='color:{TEXT_MUTED}; font-size:11px; margin:0;'>Score</p>
                        <p style='color:{TEXT_PRIMARY}; font-size:20px; font-weight:700; margin:0;'>{rt_risk['risk_score']}/100</p>
                    </div>
                    <div>
                        <p style='color:{TEXT_MUTED}; font-size:11px; margin:0;'>Level</p>
                        <p style='color:{get_status_color(rt_risk["risk_level"])}; font-size:20px; font-weight:700; margin:0;'>{rt_risk['risk_level']}</p>
                    </div>
                    <div>
                        <p style='color:{TEXT_MUTED}; font-size:11px; margin:0;'>Regime</p>
                        <p style='color:{TEXT_PRIMARY}; font-size:20px; font-weight:700; margin:0;'>{rt_risk.get('regime', 'N/A')}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    render_realtime_alerts()

st.markdown(render_footer(last_update=last_db_update), unsafe_allow_html=True)
