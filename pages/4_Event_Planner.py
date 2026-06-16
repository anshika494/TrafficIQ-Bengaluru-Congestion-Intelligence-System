"""
pages/4_Event_Planner.py — Planned Event Deployment Planner
Generates full deployment plan with resources, timeline, diversions, 
and communication plan. Includes PDF + clipboard export.
"""

import streamlit as st
import pandas as pd
from datetime import date, time, datetime
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.risk_model import (
    compute_risk_score,
    DIVERSION_ROUTES,
    CORRIDOR_WEIGHTS,
)
from utils.pdf_export import generate_event_planner_pdf

# ──────────────────────────────────────────────
# PAGE CONFIG & CSS
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Event Planner — TrafficIQ",
    page_icon="📋",
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

.plan-header {
    background: linear-gradient(135deg, #1A2035 0%, #1E2845 100%);
    border: 1px solid rgba(226,75,74,0.3);
    border-left: 4px solid #E24B4A;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 16px;
}

.plan-card {
    background: linear-gradient(135deg, #1A2035 0%, #1E2845 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 14px;
}

.plan-section-title {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 700;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}

.resource-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}

.resource-row:last-child { border-bottom: none; }

.timeline-row {
    display: flex;
    align-items: flex-start;
    margin: 6px 0;
    font-size: 0.88rem;
}

.timeline-time {
    min-width: 70px;
    font-weight: 700;
    color: #E24B4A;
    font-size: 0.82rem;
}

.route-arrow {
    color: #3498DB;
    font-weight: 700;
    font-size: 1rem;
    margin: 0 8px;
}

.risk-badge-plan {
    display: inline-block;
    padding: 5px 16px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:12px 0 20px 0;">
        <div style="font-size:2rem;">📋</div>
        <div style="font-weight:700; color:#E24B4A;">Event Planner</div>
        <div style="font-size:0.75rem; color:#9BA3AF;">Planned deployment generator</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### ℹ️ How to Use")
    st.markdown("""
    <div style="font-size:0.82rem; color:#9BA3AF; line-height:1.7;">
    1. Fill in the event details in the left panel<br>
    2. Click <b>Generate Deployment Plan</b><br>
    3. Review the auto-generated resources, timeline, and diversions<br>
    4. Export as PDF or copy to clipboard
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PAGE TITLE
# ──────────────────────────────────────────────
st.markdown('<p class="page-title">📋 Planned Event Deployment Planner</p>', unsafe_allow_html=True)
st.markdown("<p style='color:#9BA3AF; margin-top:-8px;'>Generate complete deployment plans for processions, events, VIP movements, and construction</p>", unsafe_allow_html=True)
st.markdown("---")

# ──────────────────────────────────────────────
# EVENT TYPE PERSONNEL BASE
# ──────────────────────────────────────────────
EVENT_TYPE_BASE_PERSONNEL = {
    "procession": 8,
    "public_event": 10,
    "vip_movement": 15,
    "protest": 12,
    "construction": 4,
    "sports_event": 20,
    "religious_event": 12,
}

CROWD_MULTIPLIER = {
    "Small (<500)": 1,
    "Medium (500–5,000)": 2,
    "Large (5,000–50,000)": 4,
    "Mega (>50,000)": 8,
}

CROWD_SIZE_NUMERIC = {
    "Small (<500)": 250,
    "Medium (500–5,000)": 2500,
    "Large (5,000–50,000)": 25000,
    "Mega (>50,000)": 75000,
}

# ──────────────────────────────────────────────
# TWO COLUMN LAYOUT
# ──────────────────────────────────────────────
col_form, col_plan = st.columns([1, 1.3], gap="large")

# ──────────────────────────────────────────────
# LEFT — INPUT FORM
# ──────────────────────────────────────────────
with col_form:
    st.markdown("### 📝 Event Details")

    event_name = st.text_input(
        "🎪 Event Name",
        value="Annual Ganesh Utsav Procession",
        help="Name or description of the planned event",
    )

    event_type_sel = st.selectbox(
        "🏷️ Event Type",
        list(EVENT_TYPE_BASE_PERSONNEL.keys()),
        format_func=lambda x: x.replace("_", " ").title(),
        help="Category of the event",
    )

    location = st.text_input(
        "📍 Location / Address",
        value="Majestic Bus Stand, Bengaluru",
        help="Primary location of the event",
    )

    all_corridors = sorted(list(set(
        list(CORRIDOR_WEIGHTS.keys()) + [
            "Bannerghatta Road", "Magadi Road", "ORR East 2", "ORR North 2",
            "ORR South", "ORR West", "Kanakapura Road", "Airport Road",
            "Whitefield Road", "Non-corridor", "Old Madras Road",
        ]
    )))

    nearest_corridor = st.selectbox(
        "🛣️ Nearest Corridor",
        all_corridors,
        index=all_corridors.index("Mysore Road") if "Mysore Road" in all_corridors else 0,
        help="Which traffic corridor is nearest to or most impacted by the event",
    )

    crowd_size = st.selectbox(
        "👥 Expected Crowd Size",
        list(CROWD_MULTIPLIER.keys()),
        index=1,
        help="Estimated number of attendees",
    )

    event_date = st.date_input(
        "📅 Event Date",
        value=date.today(),
        help="Date of the event",
    )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        start_time_input = st.time_input("⏰ Start Time", value=time(18, 0))
    with col_t2:
        end_time_input = st.time_input("🏁 End Time", value=time(22, 0))

    is_night = st.toggle(
        "🌙 Night Event",
        value=True,
        help="Toggle if event is primarily during night hours",
    )

    road_closure_expected = st.radio(
        "🚧 Expected Road Closure",
        ["Yes", "No"],
        horizontal=True,
        help="Will roads be closed for this event?",
    )

    st.markdown("---")
    generate_btn = st.button(
        "🚀 Generate Deployment Plan",
        width='stretch',
        type="primary",
    )

# ──────────────────────────────────────────────
# RIGHT — DEPLOYMENT PLAN
# ──────────────────────────────────────────────
with col_plan:
    st.markdown("### 📊 Deployment Plan")

    # Always compute (reactive)
    requires_closure = road_closure_expected == "Yes"
    hour_val = start_time_input.hour
    crowd_numeric = CROWD_SIZE_NUMERIC[crowd_size]
    crowd_mult = CROWD_MULTIPLIER[crowd_size]
    base_personnel = EVENT_TYPE_BASE_PERSONNEL[event_type_sel]
    total_personnel = base_personnel * crowd_mult

    # Risk score for this event
    risk_result = compute_risk_score(
        corridor=nearest_corridor,
        event_cause=event_type_sel if event_type_sel in ["protest", "procession", "vip_movement", "public_event", "construction"] else "public_event",
        day_of_week=event_date.strftime("%A"),
        hour=hour_val,
        event_type="planned",
        requires_road_closure=requires_closure,
    )

    risk_score = risk_result["score"]
    risk_label = risk_result["label"]
    risk_color = risk_result["color"]

    # Resources
    vehicles = max(1, total_personnel // 6)
    barricade_units = max(1, total_personnel // 3)
    first_aid_posts = 1 + (1 if crowd_numeric > 5000 else 0) + (1 if crowd_numeric > 50000 else 0)
    traffic_marshals = max(1, total_personnel // 4)
    ambulances = 1 + max(0, crowd_numeric // 5000)

    # Communication requirements
    btmc_required = crowd_numeric >= 5000
    media_advisory = crowd_numeric > 5000
    vip_protocol = event_type_sel == "vip_movement"

    # Diversion routes
    diversions = DIVERSION_ROUTES.get(nearest_corridor, ["→ Via alternate arterial road", "→ Via parallel connecting road"])
    primary_divs = diversions[:2]
    secondary_div = diversions[-1] if len(diversions) > 1 else "→ Via nearest alternate route"

    # ── PLAN HEADER ──
    date_str = event_date.strftime("%d %b %Y")
    st.markdown(f"""
    <div class="plan-header">
        <div style="font-size:1.2rem; font-weight:800; color:#FAFAFA; margin-bottom:4px;">
            🎪 {event_name}
        </div>
        <div style="font-size:0.88rem; color:#9BA3AF; margin-bottom:10px;">
            📍 {location} &nbsp;·&nbsp; 📅 {date_str} &nbsp;·&nbsp; 
            ⏰ {start_time_input.strftime('%H:%M')} – {end_time_input.strftime('%H:%M')}
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <span class="risk-badge-plan" style="background:rgba({
                '226,75,74' if risk_score >= 85 else
                '230,126,34' if risk_score >= 70 else
                '243,156,18' if risk_score >= 40 else
                '39,174,96'
            },0.2); color:{risk_color}; border:1px solid {risk_color};">
                Risk: {risk_label} ({risk_score}/100)
            </span>
            <span style="background:rgba(52,152,219,0.2); color:#3498DB; border:1px solid rgba(52,152,219,0.4); 
                         padding:5px 16px; border-radius:20px; font-size:0.85rem; font-weight:600;">
                {crowd_size}
            </span>
            <span style="background:rgba(155,89,182,0.2); color:#9B59B6; border:1px solid rgba(155,89,182,0.4);
                         padding:5px 16px; border-radius:20px; font-size:0.85rem; font-weight:600;">
                {event_type_sel.replace('_',' ').title()}
            </span>
            {'<span style="background:rgba(226,75,74,0.2); color:#E24B4A; border:1px solid rgba(226,75,74,0.4); padding:5px 16px; border-radius:20px; font-size:0.85rem; font-weight:600;">🚧 Road Closure</span>' if requires_closure else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── RESOURCE REQUIREMENTS ──
    st.markdown(f"""
    <div class="plan-card">
        <div class="plan-section-title" style="color:#27AE60;">👮 Resource Requirements</div>
        <div class="resource-row">
            <span style="color:#9BA3AF;">Personnel (Officers)</span>
            <span style="color:#FAFAFA; font-weight:700; font-size:1.15rem;">{total_personnel}</span>
        </div>
        <div class="resource-row">
            <span style="color:#9BA3AF;">Vehicles</span>
            <span style="color:#FAFAFA; font-weight:700;">{vehicles}</span>
        </div>
        <div class="resource-row">
            <span style="color:#9BA3AF;">Barricade Units</span>
            <span style="color:#FAFAFA; font-weight:700;">{barricade_units}</span>
        </div>
        <div class="resource-row">
            <span style="color:#9BA3AF;">First Aid Posts</span>
            <span style="color:#FAFAFA; font-weight:700;">{first_aid_posts}</span>
        </div>
        <div class="resource-row">
            <span style="color:#9BA3AF;">Traffic Marshals</span>
            <span style="color:#FAFAFA; font-weight:700;">{traffic_marshals}</span>
        </div>
        <div class="resource-row">
            <span style="color:#9BA3AF;">Ambulances</span>
            <span style="color:#FAFAFA; font-weight:700;">{ambulances} pre-positioned</span>
        </div>
        <div style="margin-top:10px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.05); 
                    font-size:0.78rem; color:#6B7280;">
            Base {base_personnel} officers × {crowd_mult}× crowd multiplier ({crowd_size})
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DEPLOYMENT TIMELINE ──
    timeline_items = [
        ("T−48h", "Route survey, dry run, and briefing"),
        ("T−24h", "Barricade deployment and zone marking"),
        ("T−6h", "Personnel deployment begins — staging areas activated"),
        ("T−2h", "Traffic diversion activated — public communication"),
        ("T−0", f"Event begins — full deployment on {nearest_corridor}"),
        ("T+End", "Gradual withdrawal begins — maintain perimeter"),
        ("T+2h", "Full clearance target — restore normal traffic flow"),
    ]
    timeline_rows = []
    for t_label, t_desc in timeline_items:
        row_color = "#27AE60" if t_label.startswith("T+") else "#E24B4A"
        timeline_rows.append(
            '<div style="display:flex; align-items:flex-start; margin:8px 0;">'
            f'<span style="min-width:70px; font-weight:700; font-size:0.82rem; color:{row_color};">{t_label}</span>'
            f'<span style="color:rgba(255,255,255,0.75); font-size:0.85rem; padding-left:8px;">{t_desc}</span>'
            "</div>"
        )
    timeline_html = "\n".join(timeline_rows)

    st.markdown(
        '<div class="plan-card">'
        '<div class="plan-section-title" style="color:#3498DB;">📅 Deployment Timeline</div>'
        + timeline_html
        + "</div>",
        unsafe_allow_html=True,
    )

    # ── DIVERSION PLAN ──
    div_primary_html = "".join([
        f'<div style="color:#FAFAFA; font-size:0.85rem; margin:5px 0; padding:6px 0;">'
        f'<span style="color:#3498DB; font-weight:700;">PRIMARY {i+1}</span> &nbsp;{d}</div>'
        for i, d in enumerate(primary_divs)
    ])

    st.markdown(f"""
    <div class="plan-card">
        <div class="plan-section-title" style="color:#9B59B6;">🔀 Diversion Plan — {nearest_corridor}</div>
        {div_primary_html}
        <div style="color:#FAFAFA; font-size:0.85rem; margin:5px 0; padding:6px 0; border-top:1px solid rgba(255,255,255,0.05); margin-top:6px;">
            <span style="color:#F7C948; font-weight:700;">SECONDARY</span> &nbsp;{secondary_div}
        </div>
        <div style="margin-top:10px; background:rgba(52,152,219,0.05); border:1px solid rgba(52,152,219,0.15); 
                    border-radius:8px; padding:10px 14px; font-size:0.82rem;">
            <div style="color:#3498DB; font-weight:700; margin-bottom:4px;">Route Diagram</div>
            <div style="color:#9BA3AF; font-family:monospace; line-height:1.8;">
                {nearest_corridor}<br>
                &nbsp;&nbsp;&nbsp;↓ Closure Point<br>
                &nbsp;&nbsp;&nbsp;├── {primary_divs[0].replace('→ ', '') if primary_divs else 'Alternate 1'}<br>
                &nbsp;&nbsp;&nbsp;├── {primary_divs[1].replace('→ ', '') if len(primary_divs) > 1 else 'Alternate 2'}<br>
                &nbsp;&nbsp;&nbsp;└── {secondary_div.replace('→ ', '')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── COMMUNICATION PLAN ──
    comm_items = []
    if btmc_required:
        comm_items.append(("🚌", "BTMC Coordination", "Required — coordinate bus diversions", "#E24B4A"))
    else:
        comm_items.append(("🚌", "BTMC Coordination", "Not required for small crowd", "#27AE60"))

    if media_advisory:
        comm_items.append(("📺", "Media Advisory", "Required — issue public notice 24h before", "#F7C948"))
    else:
        comm_items.append(("📺", "Media Advisory", "Optional — social media advisory sufficient", "#27AE60"))

    if vip_protocol:
        comm_items.append(("🎖️", "VIP Protocol Unit", "Required — coordinate with security detail", "#9B59B6"))

    comm_items.append(("🚑", "Ambulances", f"{ambulances} unit(s) pre-positioned at event perimeter", "#27AE60"))
    comm_items.append(("📻", "Radio Coordination", f"PCR van on standby — Zone Control informed", "#3498DB"))
    comm_items.append(("📱", "Public Alert", f"Disha alert issued for {nearest_corridor} route", "#3498DB"))

    comm_html = "".join([
        f'<div class="resource-row">'
        f'<span style="font-size:1.1rem; margin-right:8px;">{icon}</span>'
        f'<span style="color:#9BA3AF; flex:1;">{label}</span>'
        f'<span style="color:{color}; font-size:0.82rem; font-weight:600; text-align:right; max-width:200px;">{value}</span>'
        f'</div>'
        for icon, label, value, color in comm_items
    ])

    st.markdown(f"""
    <div class="plan-card">
        <div class="plan-section-title" style="color:#F7C948;">📡 Communication Plan</div>
        {comm_html}
    </div>
    """, unsafe_allow_html=True)

    # ── EXPORT BUTTONS ──
    st.markdown("---")
    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        if st.button("📄 Generate PDF Report", width='stretch', type="secondary"):
            with st.spinner("Generating PDF..."):
                try:
                    pdf_bytes = generate_event_planner_pdf(
                        event_name=event_name,
                        event_type=event_type_sel.replace("_", " ").title(),
                        location=location,
                        corridor=nearest_corridor,
                        crowd_size=crowd_size,
                        event_date=date_str,
                        start_time=start_time_input.strftime("%H:%M"),
                        end_time=end_time_input.strftime("%H:%M"),
                        risk_score=risk_score,
                        risk_label=risk_label,
                        personnel=total_personnel,
                        vehicles=vehicles,
                        barricade_units=barricade_units,
                        first_aid_posts=first_aid_posts,
                        traffic_marshals=traffic_marshals,
                        primary_diversions=primary_divs,
                        secondary_diversion=secondary_div,
                        btmc_required=btmc_required,
                        media_advisory=media_advisory,
                        vip_protocol=vip_protocol,
                        ambulances=ambulances,
                    )
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=f"event_plan_{event_name.replace(' ', '_')[:20]}_{date_str.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        width='stretch',
                    )
                except Exception as e:
                    st.error(f"PDF error: {e}")

    with exp_col2:
        plan_text = f"""TRAFFICIQ — EVENT DEPLOYMENT PLAN
{'='*50}
Event: {event_name}
Location: {location}
Date: {date_str}
Time: {start_time_input.strftime('%H:%M')} – {end_time_input.strftime('%H:%M')}
Risk Level: {risk_label} ({risk_score}/100)

RESOURCES
Personnel: {total_personnel}
Vehicles: {vehicles}
Barricades: {barricade_units} units
First Aid Posts: {first_aid_posts}
Marshals: {traffic_marshals}
Ambulances: {ambulances}

DIVERSIONS
Primary: {'; '.join(primary_divs)}
Secondary: {secondary_div}

COMMUNICATION
BTMC: {'Required' if btmc_required else 'Not Required'}
Media Advisory: {'Required' if media_advisory else 'Not Required'}
VIP Protocol: {'Required' if vip_protocol else 'Not Required'}
"""
        st.download_button(
            label="📋 Download as Text",
            data=plan_text,
            file_name=f"event_plan_{event_name.replace(' ', '_')[:20]}.txt",
            mime="text/plain",
            width='stretch',
        )

st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#6B7280; font-size:0.78rem; padding:8px 0;'>
    📋 TrafficIQ Event Planner · Bengaluru Traffic Police EDCI System
</div>
""", unsafe_allow_html=True)
