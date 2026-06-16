"""
pages/2_Risk_Forecaster.py — Congestion Risk Forecaster
Formula-driven risk scoring; works entirely without CSV.
"""

import streamlit as st
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.risk_model import (
    compute_risk_score,
    predict_resolution_time,
    generate_deployment_recommendation,
    CAUSE_WEIGHTS,
    CORRIDOR_WEIGHTS,
    DIVERSION_ROUTES,
    BARRICADE_POINTS,
)
from utils.pdf_export import generate_risk_forecaster_pdf

# ──────────────────────────────────────────────
# PAGE CONFIG & CSS
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Risk Forecaster — TrafficIQ",
    page_icon="🎯",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.risk-card {
    background: linear-gradient(135deg, #1A2035 0%, #1E2845 100%);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.07);
}

.risk-score-display {
    text-align: center;
    padding: 20px;
}

.risk-score-number {
    font-size: 5rem;
    font-weight: 900;
    line-height: 1;
}

.risk-badge {
    display: inline-block;
    padding: 6px 20px;
    border-radius: 20px;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    margin-top: 8px;
}

.section-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6B7280;
    margin-bottom: 4px;
    font-weight: 600;
}

.rec-box {
    background: linear-gradient(135deg, rgba(26,32,53,0.95) 0%, rgba(30,40,69,0.95) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 14px;
}

.rec-box h4 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 12px 0;
}

.metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}

.metric-row:last-child { border-bottom: none; }

.breakdown-bar {
    height: 8px;
    border-radius: 4px;
    margin: 3px 0;
}

.page-title {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #E24B4A, #FF6B35);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:12px 0 20px 0;">
        <div style="font-size:2rem;">🎯</div>
        <div style="font-weight:700; color:#E24B4A;">Risk Forecaster</div>
        <div style="font-size:0.75rem; color:#9BA3AF;">Formula-driven congestion risk</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### ℹ️ About")
    st.markdown("""
    <div style="font-size:0.82rem; color:#9BA3AF; line-height:1.6;">
    This forecaster uses a weighted formula based on historical patterns from 
    8,173 Bengaluru traffic events (Nov 2023 – Apr 2024).<br><br>
    Risk Score = Base + Peak Hour + Day + Cause + Closure + Type + Corridor
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PAGE TITLE
# ──────────────────────────────────────────────
st.markdown('<p class="page-title">🎯 Congestion Risk Forecaster</p>', unsafe_allow_html=True)
st.markdown("<p style='color:#9BA3AF; margin-top:-8px;'>Enter event parameters to compute AI-driven risk score and deployment recommendations</p>", unsafe_allow_html=True)
st.markdown("---")

# ──────────────────────────────────────────────
# TWO-COLUMN LAYOUT
# ──────────────────────────────────────────────
col_inputs, col_outputs = st.columns([1, 1.4], gap="large")

# ──────────────────────────────────────────────
# LEFT — INPUTS
# ──────────────────────────────────────────────
with col_inputs:
    st.markdown("### 📝 Event Parameters")

    all_corridors = sorted(list(set(
        list(CORRIDOR_WEIGHTS.keys()) + [
            "Bannerghatta Road", "Magadi Road", "ORR East 2", "ORR North 2",
            "ORR South", "ORR West", "Kanakapura Road", "Doddaballapur Road",
            "Airport Road", "Whitefield Road", "Non-corridor",
        ]
    )))

    corridor = st.selectbox(
        "🛣️ Corridor",
        all_corridors,
        index=all_corridors.index("Mysore Road") if "Mysore Road" in all_corridors else 0,
        help="Select the affected traffic corridor",
    )

    all_causes = sorted(list(CAUSE_WEIGHTS.keys()))
    event_cause = st.selectbox(
        "⚠️ Event Cause",
        all_causes,
        index=all_causes.index("vehicle_breakdown") if "vehicle_breakdown" in all_causes else 0,
        help="Primary cause of the traffic event",
    )

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_of_week = st.selectbox(
        "📆 Day of Week",
        days_of_week,
        index=3,  # Thursday (peak)
        help="Day when the event occurs",
    )

    hour = st.slider(
        "⏰ Hour of Day",
        min_value=0,
        max_value=23,
        value=21,
        format="%d:00",
        help="Hour when the event starts (24h format)",
    )
    st.caption(f"Selected: **{hour:02d}:00** {'🔴 Peak Hour' if hour in [20,21,22,23,0,1,2,3,4,5,6] else '🟢 Off-Peak'}")

    event_type = st.radio(
        "📌 Event Type",
        ["unplanned", "planned"],
        format_func=lambda x: f"{'🔴 Unplanned' if x == 'unplanned' else '🟢 Planned'}",
        help="Whether the event was anticipated",
        horizontal=True,
    )

    requires_road_closure = st.checkbox(
        "🚧 Road Closure Expected",
        value=False,
        help="Will the event require closing a road?",
    )

    duration_hrs = st.number_input(
        "⏳ Expected Event Duration (hours)",
        min_value=0.1,
        max_value=720.0,
        value=2.0,
        step=0.5,
        help="Estimated duration of the event in hours",
    )

    st.markdown("---")
    compute_btn = st.button(
        "🔮 Compute Risk & Generate Plan",
        width='stretch',
        type="primary",
    )

# ──────────────────────────────────────────────
# RIGHT — OUTPUTS
# ──────────────────────────────────────────────
with col_outputs:
    st.markdown("### 📊 Risk Analysis & Deployment Plan")

    # Auto-compute on any input change (reactive)
    risk_result = compute_risk_score(
        corridor=corridor,
        event_cause=event_cause,
        day_of_week=day_of_week,
        hour=hour,
        event_type=event_type,
        requires_road_closure=requires_road_closure,
        duration_hrs=duration_hrs,
    )

    resolution_result = predict_resolution_time(
        event_cause=event_cause,
        is_peak_hour=risk_result["is_peak"],
        requires_road_closure=requires_road_closure,
        event_type=event_type,
    )

    recommendation = generate_deployment_recommendation(
        corridor=corridor,
        event_cause=event_cause,
        risk_score=risk_result["score"],
        is_peak_hour=risk_result["is_peak"],
        requires_road_closure=requires_road_closure,
    )

    # ── SECTION A — Risk Score ──
    score = risk_result["score"]
    label = risk_result["label"]
    color = risk_result["color"]

    st.markdown(f"""
    <div class="risk-card">
        <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:#9BA3AF; margin-bottom:12px;">
            🎯 SECTION A — RISK SCORE
        </div>
        <div class="risk-score-display">
            <div class="risk-score-number" style="color:{color};">{score}</div>
            <div style="color:#9BA3AF; font-size:0.85rem;">out of 100</div>
            <div class="risk-badge" style="background:rgba({
                '226,75,74' if score >= 85 else
                '230,126,34' if score >= 70 else
                '243,156,18' if score >= 40 else
                '39,174,96'
            },0.2); color:{color}; border:1px solid {color};">
                {label}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Risk gauge chart
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#9BA3AF",
                "tickfont": dict(color="#9BA3AF"),
            },
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "rgba(26,32,53,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "rgba(39,174,96,0.15)"},
                {"range": [40, 70], "color": "rgba(243,156,18,0.15)"},
                {"range": [70, 85], "color": "rgba(230,126,34,0.15)"},
                {"range": [85, 100], "color": "rgba(226,75,74,0.2)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
        number={"font": {"color": color, "size": 36, "family": "Inter"}, "suffix": "/100"},
        title={"text": f"Risk Level: <b>{label}</b>", "font": {"color": "#FAFAFA", "size": 13}},
    ))
    fig_gauge.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(26,32,53,0.9)",
        margin=dict(t=30, b=20, l=20, r=20),
        height=220,
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig_gauge, width='stretch')

    # Score breakdown
    with st.expander("📊 View Score Breakdown", expanded=False):
        breakdown = risk_result["breakdown"]
        total_shown = 0
        for component, value in breakdown.items():
            if value > 0:
                pct = value / 100
                bar_w = int(pct * 20)
                st.markdown(f"""
                <div style="margin: 4px 0;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                        <span style="font-size:0.82rem; color:#FAFAFA;">{component}</span>
                        <span style="font-size:0.82rem; color:#E24B4A; font-weight:700;">+{value}</span>
                    </div>
                    <div style="height:6px; background:rgba(255,255,255,0.06); border-radius:3px;">
                        <div style="height:6px; width:{min(value, 30)*3}%; background:#E24B4A; border-radius:3px; opacity:0.8;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── SECTION B — Resolution Time ──
    st.markdown(f"""
    <div class="risk-card" style="margin-top:12px;">
        <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:#9BA3AF; margin-bottom:12px;">
            ⏱️ SECTION B — PREDICTED RESOLUTION TIME
        </div>
        <div style="text-align:center;">
            <div style="font-size:2.4rem; font-weight:800; color:#3498DB;">{resolution_result['formatted']}</div>
            <div style="color:#9BA3AF; font-size:0.82rem; margin-top:6px;">
                Base: {event_cause.replace('_',' ').title()} median · 
                {'🔴 ×1.3 peak hour' if risk_result['is_peak'] else ''} 
                {'🚧 ×1.2 road closure' if requires_road_closure else ''}
                {'🟢 ×0.9 planned' if event_type == 'planned' else ''}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SECTION C — Deployment Recommendation ──
    st.markdown("""
    <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:#9BA3AF; margin: 12px 0 8px 0;">
        🚔 SECTION C — AI DEPLOYMENT RECOMMENDATION
    </div>
    """, unsafe_allow_html=True)

    if score >= 85:
        st.error(f"🚨 **CRITICAL RISK** — Maximum deployment required on {corridor}")
    elif score >= 70:
        st.warning(f"⚠️ **HIGH RISK** — Enhanced deployment required on {corridor}")
    elif score >= 40:
        st.warning(f"🟡 **MODERATE RISK** — Standard deployment with monitoring on {corridor}")
    else:
        st.success(f"✅ **LOW RISK** — Minimal deployment sufficient on {corridor}")

    # Resource summary
    st.markdown(f"""
    <div class="rec-box">
        <h4 style="color:#27AE60;">👮 Resource Requirements</h4>
        <div class="metric-row">
            <span style="color:#9BA3AF; font-size:0.88rem;">Personnel Required</span>
            <span style="color:#FAFAFA; font-weight:700; font-size:1.1rem;">{recommendation['personnel']} officers</span>
        </div>
        <div class="metric-row">
            <span style="color:#9BA3AF; font-size:0.88rem;">Alert Zone Radius</span>
            <span style="color:#FAFAFA; font-weight:700;">{recommendation['alert_radius_km']} km</span>
        </div>
        <div class="metric-row">
            <span style="color:#9BA3AF; font-size:0.88rem;">Peak Hour Status</span>
            <span style="color:{'#E24B4A' if risk_result['is_peak'] else '#27AE60'}; font-weight:700;">
                {'🔴 PEAK HOUR' if risk_result['is_peak'] else '🟢 OFF-PEAK'}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Barricade points
    barricade_items = "".join([f"<li style='margin:4px 0; color:#FAFAFA; font-size:0.85rem;'>📍 {b}</li>" for b in recommendation['barricades']])
    st.markdown(f"""
    <div class="rec-box">
        <h4 style="color:#F7C948;">🚧 Barricade Points</h4>
        <ul style="margin:0; padding-left:16px; list-style:none;">
            {barricade_items}
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Diversion routes
    diversion_items = "".join([f"<li style='margin:6px 0; color:#FAFAFA; font-size:0.85rem;'>{d}</li>" for d in recommendation['diversions']])
    st.markdown(f"""
    <div class="rec-box">
        <h4 style="color:#3498DB;">🔀 Diversion Routes</h4>
        <ul style="margin:0; padding-left:0; list-style:none;">
            {diversion_items}
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Special flags
    if recommendation["flags"]:
        flag_items = "".join([f"<li style='margin:6px 0; color:#F7C948; font-size:0.85rem;'>{f}</li>" for f in recommendation["flags"]])
        st.markdown(f"""
        <div class="rec-box" style="border-color:rgba(247,201,72,0.2);">
            <h4 style="color:#F7C948;">⚡ Special Flags</h4>
            <ul style="margin:0; padding-left:0; list-style:none;">
                {flag_items}
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # ── PDF EXPORT ──
    st.markdown("---")
    if st.button("📄 Download Deployment Plan as PDF", width='stretch', type="secondary"):
        with st.spinner("Generating PDF..."):
            try:
                pdf_bytes = generate_risk_forecaster_pdf(
                    corridor=corridor,
                    event_cause=event_cause,
                    day_of_week=day_of_week,
                    hour=hour,
                    event_type=event_type,
                    requires_road_closure=requires_road_closure,
                    risk_score=score,
                    risk_label=label,
                    resolution_formatted=resolution_result["formatted"],
                    personnel=recommendation["personnel"],
                    barricades=recommendation["barricades"],
                    diversions=recommendation["diversions"],
                    alert_radius_km=recommendation["alert_radius_km"],
                    flags=recommendation["flags"],
                )
                st.download_button(
                    label="⬇️ Click to Download PDF",
                    data=pdf_bytes,
                    file_name=f"deployment_plan_{corridor.replace(' ', '_')}_{hour:02d}h.pdf",
                    mime="application/pdf",
                    width='stretch',
                )
            except Exception as e:
                st.error(f"PDF generation error: {e}")

st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#6B7280; font-size:0.78rem; padding:8px 0;'>
    🎯 TrafficIQ Risk Forecaster · Bengaluru Traffic Police EDCI System
</div>
""", unsafe_allow_html=True)
