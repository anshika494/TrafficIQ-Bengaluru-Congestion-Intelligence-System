"""
app.py — TrafficIQ: Bengaluru Congestion Intelligence System
Entry point with overview dashboard.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import sys
import os

# Add project root to path for utils imports
sys.path.insert(0, os.path.dirname(__file__))

from utils.data_loader import load_data, get_summary_stats

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="TrafficIQ — Bengaluru Congestion Intelligence",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1A2035 0%, #1E2845 100%);
    border: 1px solid rgba(226,75,74,0.2);
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(226,75,74,0.15);
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    color: #E24B4A !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #9BA3AF !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1421 0%, #111827 100%);
    border-right: 1px solid rgba(226,75,74,0.2);
}

/* Alert / banner */
.insight-banner {
    background: linear-gradient(135deg, rgba(226,75,74,0.15) 0%, rgba(255,107,53,0.1) 100%);
    border: 1px solid rgba(226,75,74,0.4);
    border-left: 4px solid #E24B4A;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px 0;
}

.insight-banner h4 {
    color: #E24B4A;
    margin: 0 0 6px 0;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.insight-banner p {
    color: #FAFAFA;
    margin: 0;
    font-size: 1rem;
    font-weight: 500;
}

/* Data freshness badge */
.freshness-badge {
    background: rgba(39,174,96,0.1);
    border: 1px solid rgba(39,174,96,0.3);
    border-radius: 20px;
    padding: 6px 14px;
    color: #27AE60;
    font-size: 0.8rem;
    font-weight: 500;
    display: inline-block;
}

/* Section headers */
.section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #FAFAFA;
    border-bottom: 2px solid #E24B4A;
    padding-bottom: 8px;
    margin: 24px 0 16px 0;
}

/* Hero area */
.hero-container {
    background: linear-gradient(135deg, #0D1421 0%, #1A2035 50%, #0D1421 100%);
    border: 1px solid rgba(226,75,74,0.3);
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}

.hero-container::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #E24B4A, #FF6B35, #F7C948, #E24B4A);
    background-size: 200% auto;
}

.hero-title {
    font-size: 2.4rem;
    font-weight: 900;
    background: linear-gradient(135deg, #E24B4A 0%, #FF6B35 50%, #F7C948 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}

.hero-subtitle {
    color: #9BA3AF;
    font-size: 1.05rem;
    margin-top: 8px;
    font-weight: 400;
}

.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #27AE60;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0D1421; }
::-webkit-scrollbar-thumb { background: #E24B4A; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────
with st.spinner("Loading Bengaluru traffic intelligence data..."):
    df = load_data()
    stats = get_summary_stats(df)

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 16px 0 24px 0;">
        <div style="font-size:2.5rem; margin-bottom:8px;">🚦</div>
        <div style="font-size:1.1rem; font-weight:800; color:#E24B4A;">TrafficIQ</div>
        <div style="font-size:0.75rem; color:#9BA3AF; margin-top:2px;">Bengaluru Congestion Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗺️ Navigation")
    st.page_link("app.py", label="🏠 Overview", icon=None)
    st.page_link("pages/1_Dashboard.py", label="📊 Analytics Dashboard", icon=None)
    st.page_link("pages/2_Risk_Forecaster.py", label="🎯 Risk Forecaster", icon=None)
    st.page_link("pages/3_Hotspot_Map.py", label="🗺️ Hotspot Map", icon=None)
    st.page_link("pages/4_Event_Planner.py", label="📋 Event Planner", icon=None)
    st.page_link("pages/5_Post_Event_Learning.py", label="🧠 Intelligence & Learning", icon=None)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.75rem; color:#6B7280; padding: 8px 0;">
        <div><span class="status-dot"></span>System Status: <span style="color:#27AE60;">Operational</span></div>
        <div style="margin-top:6px;">Data Source: Bengaluru Traffic Police</div>
        <div style="margin-top:4px;">EDCI — Event-Driven Congestion Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# HERO SECTION
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <p class="hero-title">🚦 TrafficIQ</p>
    <p class="hero-subtitle">AI-powered event impact forecasting and enforcement planning for Bengaluru</p>
    <div style="margin-top:16px; display:flex; gap:12px; flex-wrap:wrap;">
        <span style="background:rgba(226,75,74,0.15); border:1px solid rgba(226,75,74,0.4); border-radius:20px; padding:4px 12px; font-size:0.78rem; color:#E24B4A;">🔴 Real-time Monitoring</span>
        <span style="background:rgba(39,174,96,0.15); border:1px solid rgba(39,174,96,0.4); border-radius:20px; padding:4px 12px; font-size:0.78rem; color:#27AE60;">🤖 AI Risk Scoring</span>
        <span style="background:rgba(52,152,219,0.15); border:1px solid rgba(52,152,219,0.4); border-radius:20px; padding:4px 12px; font-size:0.78rem; color:#3498DB;">📊 Pattern Intelligence</span>
        <span style="background:rgba(243,156,18,0.15); border:1px solid rgba(243,156,18,0.4); border-radius:20px; padding:4px 12px; font-size:0.78rem; color:#F39C12;">⚡ Proactive Deployment</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# METRIC CARDS
# ──────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📍 Total Events",
        value=f"{stats['total_events']:,}",
        delta="Nov 2023 – Apr 2024",
    )

with col2:
    st.metric(
        label="🔴 Currently Active",
        value=f"{stats['active_events']:,}",
        delta=f"{stats['active_events']/stats['total_events']*100:.1f}% of all events",
        delta_color="inverse",
    )

with col3:
    st.metric(
        label="🚧 Road Closures",
        value=f"{stats['road_closures']:,}",
        delta=f"{stats['road_closures']/stats['total_events']*100:.1f}% closure rate",
        delta_color="inverse",
    )

with col4:
    st.metric(
        label="⚠️ High Priority",
        value=f"{stats['high_priority']:,}",
        delta=f"{stats['high_priority']/stats['total_events']*100:.1f}% of events",
        delta_color="inverse",
    )

# ──────────────────────────────────────────────
# QUICK INSIGHT BANNER
# ──────────────────────────────────────────────
# Compute dynamic insight
top_corridor = (
    df[df["hour"].isin([20, 21, 22, 23])]
    .groupby("corridor")
    .size()
    .idxmax()
)
peak_hour_count = df[df["hour"] == 21].shape[0]
top_cause = df["event_cause"].value_counts().index[0]
top_zone_row = df.groupby("zone")["priority"].apply(
    lambda x: (x == "High").sum()
).idxmax()

st.markdown(f"""
<div class="insight-banner">
    <h4>⚡ Live Intelligence Insight</h4>
    <p>Peak congestion risk: <strong>{top_corridor}</strong> corridor between <strong>8–10 PM</strong> 
    based on historical patterns · <strong>{peak_hour_count}</strong> events historically recorded at 21:00h · 
    Most common cause: <strong>{top_cause.replace('_', ' ').title()}</strong> · 
    Highest-risk zone: <strong>{top_zone_row}</strong></p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# DATA FRESHNESS + OVERVIEW STATS
# ──────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown('<div class="section-header">📈 Dataset Overview</div>', unsafe_allow_html=True)

    date_min_str = stats["date_min"].strftime("%d %b %Y") if pd.notna(stats["date_min"]) else "N/A"
    date_max_str = stats["date_max"].strftime("%d %b %Y") if pd.notna(stats["date_max"]) else "N/A"

    ov_col1, ov_col2, ov_col3 = st.columns(3)

    event_type_counts = df["event_type"].value_counts()
    unplanned = int(event_type_counts.get("unplanned", 0))
    planned = int(event_type_counts.get("planned", 0))

    with ov_col1:
        st.markdown(f"""
        <div style="background:#1A2035; border-radius:10px; padding:16px; border:1px solid rgba(255,255,255,0.05);">
            <div style="font-size:0.75rem; color:#9BA3AF; text-transform:uppercase; letter-spacing:0.08em;">Unplanned Events</div>
            <div style="font-size:1.8rem; font-weight:800; color:#E24B4A; margin-top:4px;">{unplanned:,}</div>
            <div style="font-size:0.8rem; color:#6B7280; margin-top:4px;">
                {unplanned/stats['total_events']*100:.1f}% of total
            </div>
        </div>
        """, unsafe_allow_html=True)

    with ov_col2:
        st.markdown(f"""
        <div style="background:#1A2035; border-radius:10px; padding:16px; border:1px solid rgba(255,255,255,0.05);">
            <div style="font-size:0.75rem; color:#9BA3AF; text-transform:uppercase; letter-spacing:0.08em;">Planned Events</div>
            <div style="font-size:1.8rem; font-weight:800; color:#3498DB; margin-top:4px;">{planned:,}</div>
            <div style="font-size:0.8rem; color:#6B7280; margin-top:4px;">
                {planned/stats['total_events']*100:.1f}% of total
            </div>
        </div>
        """, unsafe_allow_html=True)

    with ov_col3:
        unique_corridors = df["corridor"].nunique()
        st.markdown(f"""
        <div style="background:#1A2035; border-radius:10px; padding:16px; border:1px solid rgba(255,255,255,0.05);">
            <div style="font-size:0.75rem; color:#9BA3AF; text-transform:uppercase; letter-spacing:0.08em;">Unique Corridors</div>
            <div style="font-size:1.8rem; font-weight:800; color:#27AE60; margin-top:4px;">{unique_corridors}</div>
            <div style="font-size:0.8rem; color:#6B7280; margin-top:4px;">Across Bengaluru</div>
        </div>
        """, unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-header">🗓️ Data Freshness</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:#1A2035; border-radius:10px; padding:20px; border:1px solid rgba(39,174,96,0.2);">
        <div class="freshness-badge">✅ Dataset Loaded</div>
        <div style="margin-top:14px;">
            <div style="font-size:0.75rem; color:#9BA3AF; text-transform:uppercase;">Date Range</div>
            <div style="font-size:0.95rem; font-weight:600; color:#FAFAFA; margin-top:4px;">{date_min_str}</div>
            <div style="font-size:0.8rem; color:#9BA3AF;">to</div>
            <div style="font-size:0.95rem; font-weight:600; color:#FAFAFA;">{date_max_str}</div>
        </div>
        <div style="margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.05);">
            <div style="font-size:0.75rem; color:#9BA3AF;">Total Records</div>
            <div style="font-size:1.2rem; font-weight:700; color:#F7C948;">{stats['total_events']:,} events</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TOP CORRIDORS SNAPSHOT
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">🛣️ Top Corridors by Event Volume</div>', unsafe_allow_html=True)

top_corridors = df.groupby("corridor").agg(
    total_events=("id", "count"),
    high_priority=("priority", lambda x: (x == "High").sum()),
    road_closures=("requires_road_closure", "sum"),
    avg_duration_hrs=("duration_hrs", "mean"),
).reset_index().sort_values("total_events", ascending=False).head(10)

top_corridors["high_pct"] = (top_corridors["high_priority"] / top_corridors["total_events"] * 100).round(1)
top_corridors["avg_duration_hrs"] = top_corridors["avg_duration_hrs"].round(1)

import plotly.express as px
import plotly.graph_objects as go

fig_corridors = go.Figure()

fig_corridors.add_trace(go.Bar(
    x=top_corridors["corridor"],
    y=top_corridors["total_events"],
    marker=dict(
        color=top_corridors["total_events"],
        colorscale="RdYlGn_r",
        showscale=False,
    ),
    text=top_corridors["total_events"],
    textposition="outside",
    textfont=dict(color="#FAFAFA", size=11),
    name="Total Events",
))

fig_corridors.update_layout(
    title=dict(
        text="Event Volume by Corridor (Top 10)",
        font=dict(size=14, color="#FAFAFA"),
    ),
    xaxis=dict(
        tickfont=dict(color="#9BA3AF", size=10),
        gridcolor="rgba(255,255,255,0.05)",
    ),
    yaxis=dict(
        title=dict(text="Event Count", font=dict(color="#9BA3AF")),
        tickfont=dict(color="#9BA3AF"),
        gridcolor="rgba(255,255,255,0.05)",
    ),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(26,32,53,0.8)",
    margin=dict(t=50, b=80, l=60, r=20),
    height=320,
    font=dict(family="Inter"),
)

st.plotly_chart(fig_corridors, use_container_width=True)

# ──────────────────────────────────────────────
# QUICK STATUS BREAKDOWN
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Quick Status Breakdown</div>', unsafe_allow_html=True)

sc1, sc2, sc3 = st.columns(3)

with sc1:
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    fig_status = px.pie(
        status_counts,
        values="Count",
        names="Status",
        title="Events by Status",
        color_discrete_map={
            "closed": "#27AE60",
            "active": "#E24B4A",
            "resolved": "#3498DB",
            "unknown": "#6B7280",
        },
        hole=0.5,
    )
    fig_status.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(26,32,53,0.8)",
        font=dict(color="#FAFAFA", family="Inter"),
        legend=dict(font=dict(color="#9BA3AF")),
        margin=dict(t=40, b=20),
        height=260,
        title_font_color="#FAFAFA",
    )
    fig_status.update_traces(textfont_color="#FAFAFA")
    st.plotly_chart(fig_status, use_container_width=True)

with sc2:
    priority_counts = df["priority"].value_counts().reset_index()
    priority_counts.columns = ["Priority", "Count"]
    fig_priority = px.pie(
        priority_counts,
        values="Count",
        names="Priority",
        title="Events by Priority",
        color_discrete_map={"High": "#E24B4A", "Low": "#3498DB"},
        hole=0.5,
    )
    fig_priority.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(26,32,53,0.8)",
        font=dict(color="#FAFAFA", family="Inter"),
        legend=dict(font=dict(color="#9BA3AF")),
        margin=dict(t=40, b=20),
        height=260,
        title_font_color="#FAFAFA",
    )
    fig_priority.update_traces(textfont_color="#FAFAFA")
    st.plotly_chart(fig_priority, use_container_width=True)

with sc3:
    top_causes = df["event_cause"].value_counts().head(7).reset_index()
    top_causes.columns = ["Cause", "Count"]
    fig_causes = px.bar(
        top_causes,
        x="Count",
        y="Cause",
        orientation="h",
        title="Top 7 Event Causes",
        color="Count",
        color_continuous_scale="RdYlGn_r",
    )
    fig_causes.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(26,32,53,0.8)",
        font=dict(color="#FAFAFA", family="Inter"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#9BA3AF")),
        yaxis=dict(tickfont=dict(color="#9BA3AF")),
        margin=dict(t=40, b=20, l=120),
        height=260,
        title_font_color="#FAFAFA",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_causes, use_container_width=True)

# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#6B7280; font-size:0.8rem; padding:12px 0;">
    🚦 <strong style="color:#E24B4A;">TrafficIQ</strong> — Bengaluru Event-Driven Congestion Intelligence System &nbsp;|&nbsp; 
    Built for Bengaluru Traffic Police &nbsp;|&nbsp; 
    Data: Nov 2023 – Apr 2024
</div>
""", unsafe_allow_html=True)
