"""
pages/1_Dashboard.py — Analytics Dashboard
All 8 charts using Plotly with full sidebar filters.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data_loader import load_data, get_corridor_list, get_cause_list

# ──────────────────────────────────────────────
# PAGE CONFIG & CSS
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Analytics Dashboard — TrafficIQ",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.chart-card {
    background: linear-gradient(135deg, #1A2035 0%, #1E2845 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 4px;
    margin-bottom: 16px;
}
.page-title {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #E24B4A, #FF6B35);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.filter-header {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6B7280;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────
with st.spinner("Loading data..."):
    df_raw = load_data()

# ──────────────────────────────────────────────
# SIDEBAR FILTERS
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:12px 0 20px 0;">
        <div style="font-size:1.8rem;">📊</div>
        <div style="font-weight:700; color:#E24B4A;">Analytics Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔍 Filters")

    # Date range
    st.markdown('<div class="filter-header">Date Range</div>', unsafe_allow_html=True)
    min_date = df_raw["start_datetime"].min().date() if df_raw["start_datetime"].notna().any() else pd.Timestamp("2023-11-01").date()
    max_date = df_raw["start_datetime"].max().date() if df_raw["start_datetime"].notna().any() else pd.Timestamp("2024-04-30").date()
    date_range = st.date_input(
        "Select date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed",
    )

    # Event type
    st.markdown('<div class="filter-header">Event Type</div>', unsafe_allow_html=True)
    event_types = df_raw["event_type"].dropna().unique().tolist()
    event_types = [e for e in event_types if e not in ["nan", "None"]]
    selected_types = st.multiselect("Event Type", event_types, default=event_types, label_visibility="collapsed")

    # Corridors
    st.markdown('<div class="filter-header">Corridors</div>', unsafe_allow_html=True)
    all_corridors = get_corridor_list(df_raw)
    selected_corridors = st.multiselect("Corridor", all_corridors, default=all_corridors, label_visibility="collapsed")

    # Priority
    st.markdown('<div class="filter-header">Priority</div>', unsafe_allow_html=True)
    priorities = ["High", "Low"]
    selected_priorities = st.multiselect("Priority", priorities, default=priorities, label_visibility="collapsed")

    # Cause
    st.markdown('<div class="filter-header">Event Cause</div>', unsafe_allow_html=True)
    all_causes = get_cause_list(df_raw)
    selected_causes = st.multiselect("Cause", all_causes, default=all_causes, label_visibility="collapsed")

    st.markdown("---")
    if st.button("🔄 Reset All Filters", use_container_width=True):
        st.rerun()

# ──────────────────────────────────────────────
# APPLY FILTERS
# ──────────────────────────────────────────────
df = df_raw.copy()

if len(date_range) == 2:
    start_dt = pd.Timestamp(date_range[0], tz="UTC")
    end_dt = pd.Timestamp(date_range[1], tz="UTC") + pd.Timedelta(days=1)
    df = df[(df["start_datetime"] >= start_dt) & (df["start_datetime"] < end_dt)]

if selected_types:
    df = df[df["event_type"].isin(selected_types)]
if selected_corridors:
    df = df[df["corridor"].isin(selected_corridors)]
if selected_priorities:
    df = df[df["priority"].isin(selected_priorities)]
if selected_causes:
    df = df[df["event_cause"].isin(selected_causes)]

# ──────────────────────────────────────────────
# PAGE TITLE
# ──────────────────────────────────────────────
st.markdown('<p class="page-title">📊 Analytics Dashboard</p>', unsafe_allow_html=True)
st.markdown(f"<p style='color:#9BA3AF; margin-top:-8px;'>Showing <strong style='color:#FAFAFA;'>{len(df):,}</strong> events · Use sidebar filters to drill down</p>", unsafe_allow_html=True)

if len(df) == 0:
    st.warning("No events match the current filter selection. Please adjust filters.")
    st.stop()

# ──────────────────────────────────────────────
# CHART COLORS HELPERS
# ──────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(26,32,53,0.95)",
    font=dict(color="#FAFAFA", family="Inter"),
    title_font=dict(color="#FAFAFA", size=14),
    legend=dict(font=dict(color="#9BA3AF", size=11)),
    margin=dict(t=50, b=40, l=60, r=20),
)

CAUSE_SEVERITY_COLOR = {
    "accident": "#E24B4A",
    "public_event": "#E24B4A",
    "protest": "#FF6B35",
    "vip_movement": "#FF6B35",
    "construction": "#F7C948",
    "water_logging": "#F7C948",
    "procession": "#F39C12",
    "congestion": "#3498DB",
    "vehicle_breakdown": "#3498DB",
    "pot_holes": "#95A5A6",
    "tree_fall": "#95A5A6",
    "road_conditions": "#95A5A6",
    "others": "#7F8C8D",
}

# ──────────────────────────────────────────────
# CHART 1 — Event Cause Distribution
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 📊 Chart 1 — Event Cause Distribution")

cause_counts = df.groupby("event_cause").size().reset_index(name="count")
cause_counts = cause_counts.sort_values("count", ascending=True)
cause_counts["color"] = cause_counts["event_cause"].map(CAUSE_SEVERITY_COLOR).fillna("#7F8C8D")

fig1 = go.Figure(go.Bar(
    x=cause_counts["count"],
    y=cause_counts["event_cause"],
    orientation="h",
    marker=dict(color=cause_counts["color"]),
    text=cause_counts["count"],
    textposition="outside",
    textfont=dict(color="#FAFAFA", size=11),
    hovertemplate="<b>%{y}</b><br>Events: %{x}<extra></extra>",
))

fig1.update_layout(
    **PLOTLY_LAYOUT,
    title="Event Cause Distribution (Sorted by Volume)",
    xaxis=dict(title="Number of Events", gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#9BA3AF")),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#FAFAFA")),
    height=450,
)

# Add severity legend annotation
fig1.add_annotation(
    text="🔴 Critical  🟠 High  🟡 Medium  🔵 Low  ⚪ Minimal",
    xref="paper", yref="paper",
    x=1, y=1.05,
    showarrow=False,
    font=dict(size=10, color="#9BA3AF"),
    align="right",
)

st.plotly_chart(fig1, use_container_width=True)

# ──────────────────────────────────────────────
# CHART 2 — Hourly Event Volume
# ──────────────────────────────────────────────
st.markdown("#### ⏰ Chart 2 — Hourly Event Volume (0–23h)")

hourly = df.groupby("hour").size().reset_index(name="count")
# Fill missing hours
all_hours = pd.DataFrame({"hour": range(24)})
hourly = all_hours.merge(hourly, on="hour", how="left").fillna(0)

fig2 = go.Figure()

# Shaded peak hour bands
fig2.add_vrect(x0=19.5, x1=23.5, fillcolor="rgba(226,75,74,0.1)", line_width=0, annotation_text="Night Peak", annotation_position="top")
fig2.add_vrect(x0=3.5, x1=7.5, fillcolor="rgba(226,75,74,0.1)", line_width=0, annotation_text="Morning Peak", annotation_position="top")

# Line chart
fig2.add_trace(go.Scatter(
    x=hourly["hour"],
    y=hourly["count"],
    mode="lines+markers",
    line=dict(color="#E24B4A", width=3),
    marker=dict(size=7, color="#E24B4A", line=dict(color="#FAFAFA", width=1)),
    fill="tozeroy",
    fillcolor="rgba(226,75,74,0.08)",
    name="Events",
    hovertemplate="Hour %{x}:00<br>Events: %{y}<extra></extra>",
))

# Annotate 21h peak
peak_val = int(hourly[hourly["hour"] == 21]["count"].values[0])
fig2.add_annotation(
    x=21, y=peak_val,
    text=f"📍 Peak: {peak_val} events",
    showarrow=True,
    arrowhead=2,
    arrowcolor="#E24B4A",
    font=dict(color="#E24B4A", size=11, family="Inter"),
    bgcolor="rgba(226,75,74,0.15)",
    bordercolor="#E24B4A",
    borderwidth=1,
    borderpad=4,
    ay=-40,
)

fig2.update_layout(
    **PLOTLY_LAYOUT,
    title="Event Frequency by Hour of Day",
    xaxis=dict(
        title="Hour of Day",
        tickvals=list(range(24)),
        ticktext=[f"{h:02d}:00" for h in range(24)],
        gridcolor="rgba(255,255,255,0.05)",
        tickfont=dict(color="#9BA3AF", size=9),
    ),
    yaxis=dict(title="Event Count", gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#9BA3AF")),
    height=380,
)

st.plotly_chart(fig2, use_container_width=True)

# ──────────────────────────────────────────────
# CHART 3 — Monthly Trend (Bar + Line Combo)
# ──────────────────────────────────────────────
st.markdown("#### 📅 Chart 3 — Monthly Event Trend")

monthly = df.groupby("month").agg(
    total_events=("id", "count"),
    road_closures=("requires_road_closure", "sum"),
).reset_index().sort_values("month")

fig3 = make_subplots(specs=[[{"secondary_y": True}]])

fig3.add_trace(
    go.Bar(
        x=monthly["month"],
        y=monthly["total_events"],
        name="Total Events",
        marker_color="#3498DB",
        opacity=0.85,
        hovertemplate="%{x}<br>Events: %{y}<extra></extra>",
    ),
    secondary_y=False,
)

fig3.add_trace(
    go.Scatter(
        x=monthly["month"],
        y=monthly["road_closures"],
        name="Road Closures",
        mode="lines+markers",
        line=dict(color="#E24B4A", width=3),
        marker=dict(size=9, color="#E24B4A", symbol="diamond"),
        hovertemplate="%{x}<br>Closures: %{y}<extra></extra>",
    ),
    secondary_y=True,
)

fig3.update_layout(
    **PLOTLY_LAYOUT,
    title="Monthly Event Volume & Road Closures",
    height=360,
    barmode="group",
)
fig3.update_xaxes(tickfont=dict(color="#9BA3AF"), gridcolor="rgba(255,255,255,0.05)")
fig3.update_yaxes(title_text="Total Events", tickfont=dict(color="#9BA3AF"), gridcolor="rgba(255,255,255,0.05)", secondary_y=False)
fig3.update_yaxes(title_text="Road Closures", tickfont=dict(color="#E24B4A"), secondary_y=True)

st.plotly_chart(fig3, use_container_width=True)

# ──────────────────────────────────────────────
# CHART 4 — Corridor Heatmap
# ──────────────────────────────────────────────
st.markdown("#### 🌡️ Chart 4 — Corridor × Hour Heatmap")

top_10_corridors = df["corridor"].value_counts().head(10).index.tolist()
heat_df = df[df["corridor"].isin(top_10_corridors)]
pivot = heat_df.pivot_table(
    index="corridor",
    columns="hour",
    values="id",
    aggfunc="count",
    fill_value=0,
)
# Ensure all hours present — use int keys to match the integer hour column
pivot.columns = pivot.columns.astype(int)
for h in range(24):
    if h not in pivot.columns:
        pivot[h] = 0
pivot = pivot[sorted(pivot.columns)]

fig4 = go.Figure(go.Heatmap(
    z=pivot.values,
    x=[f"{int(h):02d}:00" for h in pivot.columns],
    y=pivot.index.tolist(),
    colorscale="RdYlGn_r",
    hoverongaps=False,
    hovertemplate="Corridor: %{y}<br>Hour: %{x}<br>Events: %{z}<extra></extra>",
    colorbar=dict(
        title=dict(text="Events", font=dict(color="#9BA3AF")),
        tickfont=dict(color="#9BA3AF"),
    ),
))

fig4.update_layout(
    **{**PLOTLY_LAYOUT, "margin": dict(t=50, b=60, l=160, r=60)},
    title="Event Density: Top 10 Corridors × Hour of Day",
    xaxis=dict(title="Hour of Day", tickfont=dict(color="#9BA3AF", size=9)),
    yaxis=dict(title="Corridor", tickfont=dict(color="#FAFAFA", size=10)),
    height=420,
)

st.plotly_chart(fig4, use_container_width=True)

# ──────────────────────────────────────────────
# CHART 5 & 6 side by side
# ──────────────────────────────────────────────
col_c5, col_c6 = st.columns(2)

with col_c5:
    st.markdown("#### 🎯 Chart 5 — Priority vs Event Type")

    pv_df = df.groupby(["event_type", "priority"]).size().reset_index(name="count")

    fig5 = px.bar(
        pv_df,
        x="event_type",
        y="count",
        color="priority",
        barmode="group",
        color_discrete_map={"High": "#E24B4A", "Low": "#3498DB"},
        title="Priority Distribution by Event Type",
        labels={"event_type": "Event Type", "count": "Event Count", "priority": "Priority"},
    )
    fig5.update_layout(
        **PLOTLY_LAYOUT,
        height=350,
        xaxis=dict(tickfont=dict(color="#FAFAFA")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#9BA3AF")),
    )
    st.plotly_chart(fig5, use_container_width=True)

with col_c6:
    st.markdown("#### 📆 Chart 6 — Day of Week Pattern")

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_df = df.groupby("day_of_week").size().reset_index(name="count")
    dow_df["day_of_week"] = pd.Categorical(dow_df["day_of_week"], categories=day_order, ordered=True)
    dow_df = dow_df.sort_values("day_of_week")

    colors_dow = [
        "#E24B4A" if d == "Thursday" else "#3498DB"
        for d in dow_df["day_of_week"]
    ]

    fig6 = go.Figure(go.Bar(
        x=dow_df["day_of_week"],
        y=dow_df["count"],
        marker_color=colors_dow,
        text=dow_df["count"],
        textposition="outside",
        textfont=dict(color="#FAFAFA", size=10),
        hovertemplate="%{x}<br>Events: %{y}<extra></extra>",
    ))

    # Annotate Thursday
    thu_val = dow_df[dow_df["day_of_week"] == "Thursday"]["count"].values
    if len(thu_val) > 0:
        fig6.add_annotation(
            x="Thursday",
            y=thu_val[0],
            text="📍 Peak Day",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#E24B4A",
            font=dict(color="#E24B4A", size=10),
            bgcolor="rgba(226,75,74,0.15)",
            bordercolor="#E24B4A",
            borderwidth=1,
            ay=-35,
        )

    fig6.update_layout(
        **PLOTLY_LAYOUT,
        title="Events by Day of Week (Thursday = Peak)",
        xaxis=dict(tickfont=dict(color="#FAFAFA")),
        yaxis=dict(title="Event Count", gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#9BA3AF")),
        height=350,
    )
    st.plotly_chart(fig6, use_container_width=True)

# ──────────────────────────────────────────────
# CHART 7 — Zone Risk Table
# ──────────────────────────────────────────────
st.markdown("#### 🗺️ Chart 7 — Zone Risk Summary Table")

zone_df = df.groupby("zone").agg(
    Total_Events=("id", "count"),
    High_Priority=("priority", lambda x: (x == "High").sum()),
    Road_Closures=("requires_road_closure", "sum"),
).reset_index()

zone_df["High_Priority_%"] = (zone_df["High_Priority"] / zone_df["Total_Events"] * 100).round(1)
zone_df["Closure_%"] = (zone_df["Road_Closures"] / zone_df["Total_Events"] * 100).round(1)
zone_df = zone_df.sort_values("Total_Events", ascending=False)
zone_df.columns = ["Zone", "Total Events", "High Priority", "Road Closures", "High Priority %", "Closure %"]

# Color-code with styled dataframe
def color_zone_row(val, col_name):
    if col_name == "High Priority %":
        if val > 70:
            return "background-color: rgba(226,75,74,0.3)"
        elif val > 50:
            return "background-color: rgba(243,156,18,0.2)"
    if col_name == "Closure %":
        if val > 10:
            return "background-color: rgba(226,75,74,0.2)"
    return ""

styled_zone = zone_df.style.map(
    lambda v: color_zone_row(v, "High Priority %"), subset=["High Priority %"]
).map(
    lambda v: color_zone_row(v, "Closure %"), subset=["Closure %"]
).format({
    "High Priority %": "{:.1f}%",
    "Closure %": "{:.1f}%",
}).set_properties(**{
    "color": "#FAFAFA",
    "background-color": "rgba(26,32,53,0.9)",
    "font-size": "13px",
})

st.dataframe(styled_zone, use_container_width=True, hide_index=True)

# ──────────────────────────────────────────────
# CHART 8 — Active Events Feed
# ──────────────────────────────────────────────
st.markdown("#### 🔴 Chart 8 — Active Events Feed")

import datetime as dt

active_df = df[df["status"] == "active"].copy()

if len(active_df) == 0:
    st.info("No active events in the current filter selection.")
else:
    now = pd.Timestamp.now(tz="UTC")
    active_df["time_since_start_hrs"] = (
        (now - active_df["start_datetime"]).dt.total_seconds() / 3600
    ).round(1)

    display_cols = ["id", "event_cause", "corridor", "zone", "priority", "time_since_start_hrs", "requires_road_closure"]
    active_display = active_df[display_cols].rename(columns={
        "id": "Event ID",
        "event_cause": "Cause",
        "corridor": "Corridor",
        "zone": "Zone",
        "priority": "Priority",
        "time_since_start_hrs": "Hours Active",
        "requires_road_closure": "Road Closure",
    }).sort_values(["Priority", "Hours Active"], ascending=[True, False])

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_priority = st.selectbox("Filter by Priority", ["All", "High", "Low"])
    with col_f2:
        filter_cause = st.selectbox("Filter by Cause", ["All"] + sorted(active_df["event_cause"].unique().tolist()))
    with col_f3:
        filter_closure = st.selectbox("Road Closure", ["All", "Yes", "No"])

    if filter_priority != "All":
        active_display = active_display[active_display["Priority"] == filter_priority]
    if filter_cause != "All":
        active_display = active_display[active_display["Cause"] == filter_cause]
    if filter_closure == "Yes":
        active_display = active_display[active_display["Road Closure"] == True]
    elif filter_closure == "No":
        active_display = active_display[active_display["Road Closure"] == False]

    st.markdown(f"**{len(active_display)} active events** · Sorted by priority then time active")

    def style_active(val, col):
        if col == "Priority" and val == "High":
            return "color: #E24B4A; font-weight: 700;"
        if col == "Road Closure" and val:
            return "color: #F7C948; font-weight: 600;"
        return ""

    styled_active = active_display.style.map(
        lambda v: style_active(v, "Priority"), subset=["Priority"]
    ).map(
        lambda v: style_active(v, "Road Closure"), subset=["Road Closure"]
    ).format({
        "Hours Active": "{:.1f}h"
    }).set_properties(**{
        "color": "#FAFAFA",
        "font-size": "12px",
    })

    st.dataframe(styled_active, use_container_width=True, hide_index=True, height=350)

st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#6B7280; font-size:0.78rem; padding:8px 0;'>
    📊 TrafficIQ Analytics Dashboard · Bengaluru Traffic Police EDCI System
</div>
""", unsafe_allow_html=True)
