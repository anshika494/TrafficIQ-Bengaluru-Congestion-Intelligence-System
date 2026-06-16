"""
pages/3_Hotspot_Map.py — Interactive Hotspot Map
Uses Folium with CartoDB dark_matter tiles, heatmap, corridor polylines, 
and event markers. Max 500 markers for performance.
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data_loader import load_data, get_cause_list, get_zone_list

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Hotspot Map — TrafficIQ",
    page_icon="🗺️",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-title {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #E24B4A, #FF6B35);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.map-stat {
    background: linear-gradient(135deg, #1A2035, #1E2845);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CORRIDOR POLYLINES (hardcoded realistic routes)
# ──────────────────────────────────────────────
CORRIDOR_ROUTES = {
    "Mysore Road": {
        "coords": [[12.97, 77.57], [12.95, 77.55], [12.93, 77.53], [12.91, 77.51]],
        "color": "#E24B4A",
    },
    "Bellary Road 1": {
        "coords": [[13.0, 77.58], [13.03, 77.585], [13.06, 77.59], [13.09, 77.595]],
        "color": "#FF6B35",
    },
    "Tumkur Road": {
        "coords": [[13.0, 77.57], [13.02, 77.55], [13.05, 77.53]],
        "color": "#F7C948",
    },
    "Hosur Road": {
        "coords": [[12.96, 77.6], [12.94, 77.62], [12.92, 77.64]],
        "color": "#4ECDC4",
    },
    "ORR North 1": {
        "coords": [[13.0, 77.65], [13.02, 77.62], [13.04, 77.59]],
        "color": "#45B7D1",
    },
}

# ──────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────
with st.spinner("Loading map data..."):
    df_raw = load_data()

# ──────────────────────────────────────────────
# SIDEBAR FILTERS
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:12px 0 20px 0;">
        <div style="font-size:2rem;">🗺️</div>
        <div style="font-weight:700; color:#E24B4A;">Hotspot Map</div>
        <div style="font-size:0.75rem; color:#9BA3AF;">Interactive spatial analysis</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔍 Map Filters")

    # Status filter
    all_statuses = ["active", "closed", "resolved"]
    selected_status = st.multiselect("Status", all_statuses, default=["active", "closed"])

    # Priority filter
    selected_priorities = st.multiselect("Priority", ["High", "Low"], default=["High", "Low"])

    # Cause filter
    all_causes = get_cause_list(df_raw)
    selected_causes = st.multiselect("Event Cause", all_causes, default=all_causes)

    # Zone filter
    all_zones = get_zone_list(df_raw)
    selected_zones = st.multiselect("Zone", all_zones, default=all_zones)

    # Date range
    min_date = df_raw["start_datetime"].min().date() if df_raw["start_datetime"].notna().any() else pd.Timestamp("2023-11-01").date()
    max_date = df_raw["start_datetime"].max().date() if df_raw["start_datetime"].notna().any() else pd.Timestamp("2024-04-30").date()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    st.markdown("---")
    st.markdown("### 🎛️ Layer Controls")
    show_markers = st.checkbox("Show Event Markers", value=True)
    show_heatmap = st.checkbox("Show Heatmap", value=True)
    show_corridors = st.checkbox("Show Corridors", value=True)

    st.markdown("---")
    st.markdown("### 🎨 Color Markers By")
    color_by = st.radio("Color scheme", ["Priority & Status", "Event Cause"], label_visibility="collapsed")

# ──────────────────────────────────────────────
# APPLY FILTERS
# ──────────────────────────────────────────────
df = df_raw.copy()

if len(date_range) == 2:
    start_dt = pd.Timestamp(date_range[0], tz="UTC")
    end_dt = pd.Timestamp(date_range[1], tz="UTC") + pd.Timedelta(days=1)
    df = df[(df["start_datetime"] >= start_dt) & (df["start_datetime"] < end_dt)]

if selected_status:
    df = df[df["status"].isin(selected_status)]
if selected_priorities:
    df = df[df["priority"].isin(selected_priorities)]
if selected_causes:
    df = df[df["event_cause"].isin(selected_causes)]
if selected_zones:
    df = df[df["zone"].isin(selected_zones + ["Unknown Zone"])]

# Keep only events with valid lat/lon
df_map = df.dropna(subset=["latitude", "longitude"]).copy()
df_map = df_map[
    (df_map["latitude"].between(-90, 90)) &
    (df_map["longitude"].between(-180, 180))
]

# Limit to 500 markers for performance
MAX_MARKERS = 500
if len(df_map) > MAX_MARKERS:
    # Prioritize active and high priority
    high = df_map[(df_map["status"] == "active") | (df_map["priority"] == "High")]
    low = df_map[(df_map["status"] != "active") & (df_map["priority"] != "High")]
    n_high = min(len(high), MAX_MARKERS)
    n_low = max(0, MAX_MARKERS - n_high)
    df_map_sample = pd.concat([
        high.sample(n_high, random_state=42) if n_high > 0 else high,
        low.sample(min(n_low, len(low)), random_state=42) if n_low > 0 else low.head(0),
    ])
    sampled = True
else:
    df_map_sample = df_map
    sampled = False

# ──────────────────────────────────────────────
# PAGE HEADER
# ──────────────────────────────────────────────
st.markdown('<p class="page-title">🗺️ Interactive Hotspot Map</p>', unsafe_allow_html=True)
st.markdown(f"<p style='color:#9BA3AF; margin-top:-8px;'>Spatial visualization of {len(df_map):,} events across Bengaluru</p>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SUMMARY STATS ROW
# ──────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.markdown(f"""
    <div class="map-stat">
        <div style="font-size:1.5rem; font-weight:800; color:#FAFAFA;">{len(df_map):,}</div>
        <div style="font-size:0.72rem; color:#9BA3AF; text-transform:uppercase;">Total Events</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    high_p = int((df_map["priority"] == "High").sum())
    st.markdown(f"""
    <div class="map-stat">
        <div style="font-size:1.5rem; font-weight:800; color:#E24B4A;">{high_p:,}</div>
        <div style="font-size:0.72rem; color:#9BA3AF; text-transform:uppercase;">High Priority</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    closures = int(df_map["requires_road_closure"].sum())
    st.markdown(f"""
    <div class="map-stat">
        <div style="font-size:1.5rem; font-weight:800; color:#F7C948;">{closures:,}</div>
        <div style="font-size:0.72rem; color:#9BA3AF; text-transform:uppercase;">Road Closures</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    active_c = int((df_map["status"] == "active").sum())
    st.markdown(f"""
    <div class="map-stat">
        <div style="font-size:1.5rem; font-weight:800; color:#FF6B35;">{active_c:,}</div>
        <div style="font-size:0.72rem; color:#9BA3AF; text-transform:uppercase;">Active Events</div>
    </div>
    """, unsafe_allow_html=True)

with m5:
    showing = len(df_map_sample)
    st.markdown(f"""
    <div class="map-stat">
        <div style="font-size:1.5rem; font-weight:800; color:#3498DB;">{showing:,}</div>
        <div style="font-size:0.72rem; color:#9BA3AF; text-transform:uppercase;">{'Sampled' if sampled else 'Showing'} Markers</div>
    </div>
    """, unsafe_allow_html=True)

if sampled:
    st.caption(f"⚡ Showing {MAX_MARKERS} of {len(df_map):,} events (prioritizing active & high-priority) for performance")

st.markdown("---")

# ──────────────────────────────────────────────
# CAUSE COLOR MAP (for color_by == "Event Cause")
# ──────────────────────────────────────────────
CAUSE_COLORS = {
    "accident": "red",
    "public_event": "darkred",
    "protest": "orange",
    "vip_movement": "purple",
    "construction": "darkgoldenrod",
    "water_logging": "darkblue",
    "procession": "darkorange",
    "congestion": "cadetblue",
    "vehicle_breakdown": "blue",
    "pot_holes": "gray",
    "tree_fall": "darkgreen",
    "road_conditions": "lightgray",
    "others": "beige",
}


def get_marker_color(row, color_by_mode):
    if color_by_mode == "Priority & Status":
        if row["priority"] == "High" and row["status"] == "active":
            return "red"
        elif row["priority"] == "High" and row["status"] == "closed":
            return "orange"
        elif row["priority"] == "Low":
            return "blue"
        else:
            return "gray"
    else:  # Event Cause
        return CAUSE_COLORS.get(row["event_cause"], "gray")


# ──────────────────────────────────────────────
# BUILD FOLIUM MAP
# ──────────────────────────────────────────────
with st.spinner("Rendering interactive map..."):
    m = folium.Map(
        location=[12.97, 77.59],
        zoom_start=11,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # ── Layer 2: Heatmap ──
    if show_heatmap and len(df_map_sample) > 0:
        heat_data = []
        for _, row in df_map_sample.iterrows():
            if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
                weight = 1
                if row["priority"] == "High":
                    weight = 2
                if row["requires_road_closure"]:
                    weight = 3
                heat_data.append([float(row["latitude"]), float(row["longitude"]), weight])

        if heat_data:
            HeatMap(
                heat_data,
                radius=15,
                blur=20,
                max_zoom=13,
                gradient={
                    "0.2": "#3498DB",
                    "0.5": "#F7C948",
                    "0.7": "#FF6B35",
                    "1.0": "#E24B4A",
                },
                name="Heatmap",
            ).add_to(m)

    # ── Layer 3: Corridor Polylines ──
    if show_corridors:
        corridor_event_counts = df_raw.groupby("corridor").size().to_dict()
        corridor_avg_dur = df_raw.groupby("corridor")["duration_hrs"].mean().to_dict()

        for corridor_name, route_info in CORRIDOR_ROUTES.items():
            event_count = corridor_event_counts.get(corridor_name, 0)
            avg_dur = corridor_avg_dur.get(corridor_name, 0)

            # Color intensity based on event count
            max_count = max(corridor_event_counts.values()) if corridor_event_counts else 1
            intensity = event_count / max_count
            if intensity > 0.7:
                line_color = "#E24B4A"
                weight = 5
            elif intensity > 0.4:
                line_color = "#F7C948"
                weight = 4
            else:
                line_color = "#27AE60"
                weight = 3

            popup_html = f"""
            <div style="font-family:sans-serif; min-width:180px; padding:8px;">
                <h4 style="margin:0 0 8px 0; color:#E24B4A;">{corridor_name}</h4>
                <div style="font-size:12px; line-height:1.8;">
                    <b>Total Events:</b> {event_count}<br>
                    <b>Avg Resolution:</b> {avg_dur:.1f} hrs<br>
                    <b>Risk Level:</b> {'🔴 High' if intensity > 0.7 else '🟡 Medium' if intensity > 0.4 else '🟢 Low'}
                </div>
            </div>
            """

            folium.PolyLine(
                locations=route_info["coords"],
                color=line_color,
                weight=weight,
                opacity=0.85,
                tooltip=corridor_name,
                popup=folium.Popup(popup_html, max_width=220),
                dash_array=None,
            ).add_to(m)

            # Add corridor label
            mid_idx = len(route_info["coords"]) // 2
            mid_coord = route_info["coords"][mid_idx]
            folium.Marker(
                location=mid_coord,
                icon=folium.DivIcon(
                    html=f'<div style="font-size:9px; font-weight:700; color:{line_color}; '
                         f'background:rgba(15,17,23,0.85); padding:2px 6px; border-radius:4px; '
                         f'border:1px solid {line_color}; white-space:nowrap;">'
                         f'{corridor_name}</div>',
                    icon_size=(120, 20),
                    icon_anchor=(60, 10),
                ),
            ).add_to(m)

    # ── Layer 1: Event Markers ──
    if show_markers and len(df_map_sample) > 0:
        for _, row in df_map_sample.iterrows():
            if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
                marker_color = get_marker_color(row, color_by)

                # Radius based on duration
                dur = row.get("duration_mins", 60)
                if pd.isna(dur):
                    dur = 60
                radius = max(3, min(18, float(dur) / 60 + 3))

                # Popup HTML
                duration_str = f"{dur/60:.1f} hrs" if pd.notna(dur) else "Unknown"
                popup_html = f"""
                <div style="font-family:sans-serif; min-width:220px; max-width:280px; padding:10px; 
                            background:#1A2035; color:#FAFAFA; border-radius:8px;">
                    <h4 style="margin:0 0 8px 0; color:#E24B4A; border-bottom:1px solid rgba(226,75,74,0.3); padding-bottom:6px;">
                        Event #{str(row.get('id','N/A'))[:8]}
                    </h4>
                    <table style="font-size:11px; line-height:1.9; width:100%;">
                        <tr><td style="color:#9BA3AF; width:45%;">Cause</td><td style="font-weight:600;">{str(row.get('event_cause','N/A')).replace('_',' ').title()}</td></tr>
                        <tr><td style="color:#9BA3AF;">Corridor</td><td>{str(row.get('corridor','N/A'))}</td></tr>
                        <tr><td style="color:#9BA3AF;">Zone</td><td>{str(row.get('zone','N/A'))}</td></tr>
                        <tr><td style="color:#9BA3AF;">Status</td><td><span style="color:{'#E24B4A' if row.get('status')=='active' else '#27AE60'}">{str(row.get('status','N/A')).upper()}</span></td></tr>
                        <tr><td style="color:#9BA3AF;">Priority</td><td><span style="color:{'#E24B4A' if row.get('priority')=='High' else '#3498DB'}; font-weight:700;">{str(row.get('priority','N/A'))}</span></td></tr>
                        <tr><td style="color:#9BA3AF;">Duration</td><td>{duration_str}</td></tr>
                        <tr><td style="color:#9BA3AF;">Road Closure</td><td>{'🚧 Yes' if row.get('requires_road_closure') else 'No'}</td></tr>
                        <tr><td style="color:#9BA3AF;">Police Stn.</td><td style="font-size:10px;">{str(row.get('police_station','N/A'))[:25]}</td></tr>
                    </table>
                </div>
                """

                tooltip_text = f"{str(row.get('event_cause','?')).replace('_',' ').title()} · {str(row.get('corridor','?'))}"

                folium.CircleMarker(
                    location=[float(row["latitude"]), float(row["longitude"])],
                    radius=radius,
                    color=marker_color,
                    fill=True,
                    fill_color=marker_color,
                    fill_opacity=0.7,
                    weight=1.5,
                    popup=folium.Popup(popup_html, max_width=290),
                    tooltip=tooltip_text,
                ).add_to(m)

    # ── Legend ──
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: rgba(15,17,23,0.92); border: 1px solid rgba(226,75,74,0.3);
                border-radius: 10px; padding: 14px 18px; font-family: sans-serif; font-size: 12px;">
        <div style="color: #E24B4A; font-weight: 700; margin-bottom: 10px; font-size: 13px;">🗺️ Legend</div>
        <div style="color: #FAFAFA; margin: 4px 0;">
            <span style="display:inline-block; width:12px; height:12px; background:red; border-radius:50%; margin-right:6px;"></span>High Priority · Active
        </div>
        <div style="color: #FAFAFA; margin: 4px 0;">
            <span style="display:inline-block; width:12px; height:12px; background:orange; border-radius:50%; margin-right:6px;"></span>High Priority · Closed
        </div>
        <div style="color: #FAFAFA; margin: 4px 0;">
            <span style="display:inline-block; width:12px; height:12px; background:#3498DB; border-radius:50%; margin-right:6px;"></span>Low Priority
        </div>
        <div style="color: #9BA3AF; margin-top:8px; font-size:10px;">Marker size ∝ Duration</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Render map
    st_folium(
        m,
        width="100%",
        height=600,
        returned_objects=[],
    )

# ──────────────────────────────────────────────
# SUMMARY FOOTER
# ──────────────────────────────────────────────
st.markdown("---")
col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    top_zone_events = df_map.groupby("zone").size().idxmax() if len(df_map) > 0 else "N/A"
    st.info(f"🏆 **Busiest Zone:** {top_zone_events}")

with col_s2:
    top_cause_map = df_map["event_cause"].value_counts().index[0] if len(df_map) > 0 else "N/A"
    st.warning(f"⚠️ **Most Common Cause:** {top_cause_map.replace('_',' ').title()}")

with col_s3:
    closure_pct = df_map["requires_road_closure"].mean() * 100 if len(df_map) > 0 else 0
    st.error(f"🚧 **Closure Rate:** {closure_pct:.1f}% of filtered events")

st.markdown("""
<div style='text-align:center; color:#6B7280; font-size:0.78rem; padding:8px 0;'>
    🗺️ TrafficIQ Hotspot Map · CartoDB Dark Matter Basemap · Bengaluru Traffic Police EDCI System
</div>
""", unsafe_allow_html=True)
