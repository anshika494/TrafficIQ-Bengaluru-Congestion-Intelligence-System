# TrafficIQ — Bengaluru Congestion Intelligence System

> **AI-powered event impact forecasting and enforcement planning for Bengaluru Traffic Police**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://trafficiq-bengaluru-congestion-intelligence-system-6zyqskmmf2n.streamlit.app/)

---

## 🚦 Overview

TrafficIQ is a production-ready, multi-page Streamlit application for **Event-Driven Congestion Intelligence (EDCI)** in Bengaluru. It transforms 8,173 historical traffic events (Nov 2023 – Apr 2024) into actionable intelligence for traffic management officers.

### Key Capabilities
- **📊 Analytics Dashboard** — 8 interactive Plotly charts with full filter controls
- **🎯 Risk Forecaster** — Formula-driven congestion risk scoring (0–100) with deployment recommendations
- **🗺️ Hotspot Map** — Interactive Folium map with heatmap, corridor polylines, and event markers
- **📋 Event Planner** — Full deployment plan generation for any planned event
- **🧠 Intelligence & Learning** — Pattern discovery, prediction accuracy, and model improvement tracker

---

## 🗂️ Project Structure

```
trafficiq/
├── app.py                          # Entry point — Overview Dashboard
├── requirements.txt                # Python dependencies
├── README.md
├── .streamlit/
│   └── config.toml                 # Dark theme configuration
├── pages/
│   ├── 1_Dashboard.py              # Analytics Dashboard (8 charts)
│   ├── 2_Risk_Forecaster.py        # AI Risk Scoring + Deployment Plans
│   ├── 3_Hotspot_Map.py            # Interactive Folium Map
│   ├── 4_Event_Planner.py          # Planned Event Deployment Planner
│   └── 5_Post_Event_Learning.py    # Intelligence & Pattern Learning
├── utils/
│   ├── __init__.py
│   ├── data_loader.py              # Cached CSV loading + derived columns
│   ├── risk_model.py               # Risk formula + resolution predictions
│   └── pdf_export.py               # PDF generation with fpdf2
└── data/
    └── events.csv                  # ← PLACE YOUR CSV FILE HERE
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/anshika494/TrafficIQ-Bengaluru-Congestion-Intelligence-System.git
cd TrafficIQ-Bengaluru-Congestion-Intelligence-System
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Add Your Data
Place your `events.csv` file in the `data/` folder:
```bash
cp /path/to/your/events.csv data/events.csv
```

### 4. Run Locally
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## ☁️ Deploy to Streamlit Community Cloud

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial TrafficIQ deployment"
   git push origin main
   ```

2. **Connect to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click **New App**
   - Select `anshika494/TrafficIQ-Bengaluru-Congestion-Intelligence-System`
   - Set **Main file path**: `app.py`
   - Click **Deploy**

3. **Add Your Data File**:
   - Include `data/events.csv` in your repository, OR
   - Use [Streamlit Secrets](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management) for private data

> **Note**: The app requires `data/events.csv` to function. The Risk Forecaster page works without data (formula-only).

---

## 📊 Dataset Format

The app expects a CSV at `data/events.csv` with these columns:

| Column | Description |
|--------|-------------|
| `id` | Unique event identifier |
| `event_type` | `planned` or `unplanned` |
| `latitude`, `longitude` | Event start coordinates |
| `event_cause` | Cause: `vehicle_breakdown`, `accident`, `construction`, etc. |
| `requires_road_closure` | Boolean flag |
| `start_datetime` | Event start (ISO 8601 with timezone) |
| `resolved_datetime` | Resolution time (if resolved) |
| `closed_datetime` | Close time (if closed) |
| `status` | `active`, `closed`, or `resolved` |
| `priority` | `High` or `Low` |
| `corridor` | Traffic corridor name |
| `zone` | Bengaluru zone identifier |
| `police_station` | Responsible police station |

**Derived columns** are computed automatically at load time.

---

## ⚙️ Technical Notes

- All data loading uses `@st.cache_data` for performance
- Map page limits to 500 markers max (prioritizing active + high-priority)
- Datetime parsing uses `utc=True, errors='coerce'` to handle mixed formats
- Negative durations are set to `NaN` automatically
- The Risk Forecaster works entirely without CSV data (form-based)
- PDF export uses `fpdf2` (no external dependencies)

---

## 🎨 Design

- **Theme**: Dark mode with `#0F1117` background and `#E24B4A` accent
- **Charts**: Plotly Express + Graph Objects (no matplotlib)
- **Map**: Folium with CartoDB dark_matter tiles

---

## 📄 License

Built for the Bengaluru Traffic Police — Event-Driven Congestion Intelligence (EDCI) System.
