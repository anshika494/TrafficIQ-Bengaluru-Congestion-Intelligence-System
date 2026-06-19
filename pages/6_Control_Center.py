"""
pages/6_Control_Center.py — Command & Control Center
Simulated live monitoring CCTV grid, What-If mitigation simulator, 
and AI Dispatch Assistant.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data_loader import load_data
from utils.risk_model import DIVERSION_ROUTES, CORRIDOR_WEIGHTS

# ──────────────────────────────────────────────
# PAGE CONFIG & CSS
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Control Center — TrafficIQ",
    page_icon="📡",
    layout="wide",
)

# Custom styles for viewports, alert badges, simulation panels, and chat UI
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif; 
}

.page-title {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #E24B4A, #9B59B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.control-header {
    background: linear-gradient(135deg, #0F1117 0%, #151821 100%);
    border: 1px solid rgba(226, 75, 74, 0.25);
    border-radius: 8px;
    padding: 12px 20px;
    margin-bottom: 20px;
}

.cctv-card {
    background: #0D0E12;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 12px;
    position: relative;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.cctv-header {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.85rem;
    color: #FAFAFA;
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    border-bottom: 1px dashed rgba(255, 255, 255, 0.15);
    padding-bottom: 4px;
}

.cctv-overlay-text {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    color: #00FF66;
    background: rgba(0, 255, 102, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
}

.cctv-overlay-alert {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    color: #FF3344;
    background: rgba(255, 51, 68, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
    animation: blinker 1.5s linear infinite;
}

@keyframes blinker {
    50% { opacity: 0; }
}

.cctv-metric-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    color: #9BA3AF;
    margin: 4px 0;
}

.cctv-metric-val {
    font-weight: 700;
    color: #FAFAFA;
}

.simulator-panel {
    background: linear-gradient(135deg, #1A2035 0%, #1E2845 100%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 20px;
    height: 100%;
}

.kpi-card-sim {
    background: rgba(15, 17, 23, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 14px;
    text-align: center;
    margin-bottom: 10px;
}

.kpi-num-sim {
    font-size: 1.6rem;
    font-weight: 800;
}

.kpi-lbl-sim {
    font-size: 0.72rem;
    color: #9BA3AF;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
}

/* Chat bubble styling */
.chat-container {
    background: #0D0E12;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 16px;
    height: 380px;
    overflow-y: auto;
    margin-bottom: 12px;
}

.user-bubble {
    background: #2D3748;
    color: #FAFAFA;
    border-radius: 12px 12px 0 12px;
    padding: 10px 14px;
    margin-bottom: 10px;
    max-width: 80%;
    margin-left: auto;
    font-size: 0.88rem;
    border: 1px solid rgba(255,255,255,0.05);
}

.assistant-bubble {
    background: linear-gradient(135deg, #1A2035, #1E2845);
    color: #FAFAFA;
    border-radius: 12px 12px 12px 0;
    padding: 10px 14px;
    margin-bottom: 10px;
    max-width: 80%;
    margin-right: auto;
    font-size: 0.88rem;
    border-left: 3px solid #E24B4A;
}

.chat-input-row {
    display: flex;
    gap: 8px;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown('<p class="page-title">📡 Command & Control Center</p>', unsafe_allow_html=True)
st.markdown("<p style='color:#9BA3AF; margin-top:-8px;'>Simulated real-time AI analytics, CCTV dispatch grid, and operational chatbot.</p>", unsafe_allow_html=True)
st.markdown("---")

# Load data for helper operations
try:
    df_raw = load_data()
except Exception:
    df_raw = pd.DataFrame()

# ──────────────────────────────────────────────
# SECTION 1: LIVE AI CCTV MONITOR GRID
# ──────────────────────────────────────────────
st.markdown("#### 📺 Live AI CCTV Monitor Grid (Junction Feeds)")

# Initialize mock traffic flow series for active graph updates
@st.cache_data(ttl=60)
def generate_camera_data():
    x_axis = [f"{i}s ago" for i in range(15, -1, -1)]
    return {
        "SB": [random.randint(70, 95) for _ in range(16)],
        "MR": [random.randint(50, 80) for _ in range(16)],
        "MJ": [random.randint(40, 65) for _ in range(16)],
        "TC": [random.randint(20, 50) for _ in range(16)]
    }

cam_data = generate_camera_data()
x_axis_labels = [f"-{i}s" for i in range(15, -1, -1)]

# Create 2x2 grid for CCTV feeds
c1, c2 = st.columns(2)
c3, c4 = st.columns(2)

# CAMERA 1: Silk Board Junction
with c1:
    st.markdown("""
    <div class="cctv-card">
        <div class="cctv-header">
            <span>CAM-101 // SILK BOARD JUNCTION</span>
            <span class="cctv-overlay-alert">● LIVE // CRITICAL</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Renders a dark, techy line chart inside the cctv viewport
    fig1 = go.Figure(go.Scatter(
        x=x_axis_labels, y=cam_data["SB"], mode="lines+markers",
        line=dict(color="#FF3344", width=2),
        marker=dict(size=4, color="#FAFAFA"),
        fill="tozeroy", fillcolor="rgba(255, 51, 68, 0.08)"
    ))
    fig1.update_layout(
        margin=dict(t=5, b=20, l=30, r=10), height=140,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#9BA3AF", size=8)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#9BA3AF", size=8), range=[0, 100]),
    )
    st.plotly_chart(fig1, width='stretch', config={"displayModeBar": False})
    
    st.markdown("""
        <div class="cctv-metric-row">
            <span>Average Speed</span>
            <span class="cctv-metric-val" style="color:#FF3344;">11 km/h</span>
        </div>
        <div class="cctv-metric-row">
            <span>Vehicular Flow Rate</span>
            <span class="cctv-metric-val">87 vehicles/min</span>
        </div>
        <div class="cctv-metric-row">
            <span>Congestion Density</span>
            <span class="cctv-metric-val">91%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("")

# CAMERA 2: Mysore Road Flyover
with c2:
    st.markdown("""
    <div class="cctv-card">
        <div class="cctv-header">
            <span>CAM-102 // MYSORE ROAD FLYOVER</span>
            <span class="cctv-overlay-alert" style="color:#FF9900; background:rgba(255,153,0,0.1);">● LIVE // CONGESTED</span>
        </div>
    """, unsafe_allow_html=True)
    
    fig2 = go.Figure(go.Scatter(
        x=x_axis_labels, y=cam_data["MR"], mode="lines+markers",
        line=dict(color="#FF9900", width=2),
        marker=dict(size=4, color="#FAFAFA"),
        fill="tozeroy", fillcolor="rgba(255, 153, 0, 0.08)"
    ))
    fig2.update_layout(
        margin=dict(t=5, b=20, l=30, r=10), height=140,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#9BA3AF", size=8)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#9BA3AF", size=8), range=[0, 100]),
    )
    st.plotly_chart(fig2, width='stretch', config={"displayModeBar": False})
    
    st.markdown("""
        <div class="cctv-metric-row">
            <span>Average Speed</span>
            <span class="cctv-metric-val" style="color:#FF9900;">19 km/h</span>
        </div>
        <div class="cctv-metric-row">
            <span>Vehicular Flow Rate</span>
            <span class="cctv-metric-val">68 vehicles/min</span>
        </div>
        <div class="cctv-metric-row">
            <span>Congestion Density</span>
            <span class="cctv-metric-val">74%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("")

# CAMERA 3: Majestic Terminal
with c3:
    st.markdown("""
    <div class="cctv-card">
        <div class="cctv-header">
            <span>CAM-103 // MAJESTIC METRO ENTRANCE</span>
            <span class="cctv-overlay-text" style="color:#F7C948; background:rgba(247,201,72,0.1);">● LIVE // STABLE</span>
        </div>
    """, unsafe_allow_html=True)
    
    fig3 = go.Figure(go.Scatter(
        x=x_axis_labels, y=cam_data["MJ"], mode="lines+markers",
        line=dict(color="#F7C948", width=2),
        marker=dict(size=4, color="#FAFAFA"),
        fill="tozeroy", fillcolor="rgba(247, 201, 72, 0.08)"
    ))
    fig3.update_layout(
        margin=dict(t=5, b=20, l=30, r=10), height=140,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#9BA3AF", size=8)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#9BA3AF", size=8), range=[0, 100]),
    )
    st.plotly_chart(fig3, width='stretch', config={"displayModeBar": False})
    
    st.markdown("""
        <div class="cctv-metric-row">
            <span>Average Speed</span>
            <span class="cctv-metric-val" style="color:#F7C948;">29 km/h</span>
        </div>
        <div class="cctv-metric-row">
            <span>Vehicular Flow Rate</span>
            <span class="cctv-metric-val">44 vehicles/min</span>
        </div>
        <div class="cctv-metric-row">
            <span>Congestion Density</span>
            <span class="cctv-metric-val">52%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("")

# CAMERA 4: Trinity Circle
with c4:
    st.markdown("""
    <div class="cctv-card">
        <div class="cctv-header">
            <span>CAM-104 // TRINITY CIRCLE</span>
            <span class="cctv-overlay-text">● LIVE // NORMAL</span>
        </div>
    """, unsafe_allow_html=True)
    
    fig4 = go.Figure(go.Scatter(
        x=x_axis_labels, y=cam_data["TC"], mode="lines+markers",
        line=dict(color="#00FF66", width=2),
        marker=dict(size=4, color="#FAFAFA"),
        fill="tozeroy", fillcolor="rgba(0, 255, 102, 0.08)"
    ))
    fig4.update_layout(
        margin=dict(t=5, b=20, l=30, r=10), height=140,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#9BA3AF", size=8)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#9BA3AF", size=8), range=[0, 100]),
    )
    st.plotly_chart(fig4, width='stretch', config={"displayModeBar": False})
    
    st.markdown("""
        <div class="cctv-metric-row">
            <span>Average Speed</span>
            <span class="cctv-metric-val" style="color:#00FF66;">42 km/h</span>
        </div>
        <div class="cctv-metric-row">
            <span>Vehicular Flow Rate</span>
            <span class="cctv-metric-val">28 vehicles/min</span>
        </div>
        <div class="cctv-metric-row">
            <span>Congestion Density</span>
            <span class="cctv-metric-val">33%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("")

st.markdown("---")

# ──────────────────────────────────────────────
# SECTION 2 & 3: WHAT-IF SIMULATOR & CHATBOT
# ──────────────────────────────────────────────
col_sim, col_chat = st.columns([1.1, 1.2], gap="large")

# Left Column: What-If Simulator
with col_sim:
    st.markdown("#### 🔮 What-If Incident Mitigation Simulator")
    
    with st.container(border=True):
        st.markdown("<p style='font-size:0.85rem; color:#9BA3AF;'>Tweak dispatch response parameters to simulate mitigation improvements on gridlock cleanup and carbon metrics.</p>", unsafe_allow_html=True)
        
        # Levers
        resp_saved = st.slider("⏱️ Dispatch Response Time Saved (mins)", min_value=0, max_value=45, value=15, step=5,
                               help="Reduction in time it takes for first responder units to arrive on site.")
        
        barricade_eff = st.slider("🚧 Barricade Setup efficiency (%)", min_value=0, max_value=100, value=60, step=10,
                                  help="Percentage score of barricade placement alignment vs standard blueprint.")
        
        diversion_eff = st.slider("🔀 Diversion Routing execution (%)", min_value=0, max_value=100, value=50, step=10,
                                  help="The efficiency and public compliance rate of route diversions.")
        
        st.markdown("---")
        
        # Simulated Calculations
        # Baseline Congestion duration: 180 minutes. Impact values represent mock vehicles affected.
        baseline_delay_mins = 180
        multiplier = 1.0 - (0.4 * (resp_saved / 45.0)) - (0.2 * (barricade_eff / 100.0)) - (0.2 * (diversion_eff / 100.0))
        simulated_delay_mins = int(baseline_delay_mins * multiplier)
        
        commuters_affected = 650
        baseline_commuter_delay_hrs = (baseline_delay_mins / 60.0) * commuters_affected
        simulated_commuter_delay_hrs = (simulated_delay_mins / 60.0) * commuters_affected
        
        hours_saved = max(0.0, baseline_commuter_delay_hrs - simulated_commuter_delay_hrs)
        co2_saved = hours_saved * 0.28  # Average of 0.28kg CO2 emitted per hour in idle gridlock
        economic_saved = hours_saved * 85.0  # Rs. 85 value per commuter hour in delays
        
        # Display KPIs
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""
            <div class="kpi-card-sim" style="border-top:3px solid #E24B4A;">
                <div class="kpi-num-sim" style="color:#E24B4A;">{simulated_delay_mins}m</div>
                <div class="kpi-lbl-sim">New Duration</div>
                <div style="font-size:0.7rem; color:#9BA3AF; margin-top:2px;">(was {baseline_delay_mins}m)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with k2:
            st.markdown(f"""
            <div class="kpi-card-sim" style="border-top:3px solid #3498DB;">
                <div class="kpi-num-sim" style="color:#3498DB;">{hours_saved:.0f}h</div>
                <div class="kpi-lbl-sim">Delay Saved</div>
                <div style="font-size:0.7rem; color:#9BA3AF; margin-top:2px;">Total hours</div>
            </div>
            """, unsafe_allow_html=True)
            
        with k3:
            st.markdown(f"""
            <div class="kpi-card-sim" style="border-top:3px solid #27AE60;">
                <div class="kpi-num-sim" style="color:#27AE60;">{co2_saved:.1f}kg</div>
                <div class="kpi-lbl-sim">CO2 Prevented</div>
                <div style="font-size:0.7rem; color:#27AE60; margin-top:2px;">Green Impact</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f"""
        <div style="background: rgba(39, 174, 96, 0.08); border: 1px solid rgba(39, 174, 96, 0.2); 
                    border-radius: 8px; padding: 12px; font-size: 0.82rem; text-align: center; color:#FAFAFA;">
            💸 <b>Economic Savings</b>: Estimated <b>Rs. {economic_saved:,.0f}</b> in fuel and time wastage prevented for this single location.
        </div>
        """, unsafe_allow_html=True)

# Right Column: AI Dispatch Assistant
with col_chat:
    st.markdown("#### 🤖 Control Room Dispatch AI Assistant")
    
    # Session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": "Welcome to TrafficIQ Dispatch Assistant. Select a quick command or type your query below to plan deployments."}
        ]
        
    # Render chat container
    chat_html = []
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            chat_html.append(f'<div class="user-bubble">{msg["content"]}</div>')
        else:
            chat_html.append(f'<div class="assistant-bubble">{msg["content"]}</div>')
            
    st.markdown(f"""
    <div class="chat-container">
        {"".join(chat_html)}
    </div>
    """, unsafe_allow_html=True)
    
    # Predefined Quick Actions
    st.markdown("<p style='font-size:0.75rem; color:#9BA3AF; margin-bottom:4px; font-weight:600;'>⚡ QUICK DISPATCH SCRIPTS</p>", unsafe_allow_html=True)
    qa_cols = st.columns(2)
    
    with qa_cols[0]:
        q1 = st.button("🚧 Silk Board Diversions", width='stretch')
        q2 = st.button("⚠️ Mysore Road Breakdown Plan", width='stretch')
        
    with qa_cols[1]:
        q3 = st.button("🚌 Draft BTMC Bus Advisory", width='stretch')
        q4 = st.button("🚨 Clear Chat Log", width='stretch')
        
    # Handle button clicks
    user_query = ""
    if q1:
        user_query = "What are the recommended diversion routes for Silk Board congestion?"
    elif q2:
        user_query = "Generate a breakdown response plan for Mysore Road."
    elif q3:
        user_query = "Draft a bus route advisory text for BTMC during high risk alerts."
    elif q4:
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": "Chat log cleared. How can I help you coordinate deployments?"}
        ]
        st.rerun()
        
    # User text input
    with st.form("chat_form", clear_on_submit=True):
        input_col1, input_col2 = st.columns([4, 1])
        with input_col1:
            typed_query = st.text_input("Ask assistant...", placeholder="Type query (e.g. recommend officers for VIP event)...", label_visibility="collapsed")
        with input_col2:
            submit_btn = st.form_submit_button("Send", width='stretch')
            
        if submit_btn and typed_query:
            user_query = typed_query
            
    # Process user query and append response
    if user_query:
        st.session_state["chat_history"].append({"role": "user", "content": user_query})
        
        # Generate simulated operational response
        response_text = ""
        q_lower = user_query.lower()
        
        if "silk board" in q_lower or "diversion" in q_lower:
            response_text = """
            <b>[TRAFFICIQ DISPATCH SCRIPT — SILK BOARD]</b><br>
            For high congestion at Silk Board Junction (CAM-101), trigger the following diversions:<br>
            • <b>Primary Route</b>: Divert HSR-bound traffic at <i>Outer Ring Road</i> via Thanisandra / alternate connectors.<br>
            • <b>Secondary Route</b>: Channel Madiwala traffic to parallel slip road.<br>
            • <b>Officer Placement</b>: Station 3 marshals at Silk Board flyover descent.
            """
        elif "mysore road" in q_lower or "breakdown" in q_lower:
            response_text = """
            <b>[TACTICAL PLAN — MYSORE ROAD INCIDENT]</b><br>
            To mitigate breakdown delays on Mysore Road corridor:<br>
            • <b>Risk Score Modifier</b>: Adds base +15 corridor weight.<br>
            • <b>Resource Profile</b>: Deploy 6 personnel, 2 patrol cruisers, and 8 barricades.<br>
            • <b>BTMC</b>: Inform nearest depot for possible bus staging delays.<br>
            • <b>Action Checklist</b>: Deploy towing crane immediately (target arrival <15 mins).
            """
        elif "bus" in q_lower or "btmc" in q_lower:
            response_text = """
            <b>[PUBLIC / BTMC ADVISORY TEXT]</b><br>
            Copy the text below for distribution to transit controls:<br>
            <i>"TRAFFICIQ ALERT: High congestion risk detected on Mysore Road corridor due to incident. Expect 15-20 min delays. BTMC routes via NICE Road connector are activated as alternate paths. Please plan transit times accordingly."</i>
            """
        else:
            response_text = f"""
            <b>[OPERATIONAL SEARCH RESULTS]</b><br>
            For query: <i>"{user_query}"</i><br>
            • <b>Resource Profile</b>: Standard base deployment recommended (8 officers, 10 barricades).<br>
            • <b>BTMC Advisory</b>: Not mandatory for minor congestions.<br>
            • <b>Alert Radius</b>: Trigger 1.0 km corridor monitoring loop.
            """
            
        st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
        st.rerun()

st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#6B7280; font-size:0.78rem; padding:8px 0;'>
    📡 TrafficIQ Control Room Monitor Center · Bengaluru Traffic Police EDCI System
</div>
""", unsafe_allow_html=True)
