import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "events.csv"

PEAK_HOURS = [20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6]

CAUSE_SEVERITY = {
    "accident": "critical",
    "public_event": "critical",
    "protest": "high",
    "vip_movement": "high",
    "construction": "medium",
    "water_logging": "medium",
    "procession": "medium",
    "congestion": "medium",
    "vehicle_breakdown": "low",
    "pot_holes": "low",
    "tree_fall": "low",
    "road_conditions": "low",
    "others": "low",
}

CORRIDOR_COLORS = {
    "Mysore Road": "#E24B4A",
    "Bellary Road 1": "#FF6B35",
    "Tumkur Road": "#F7C948",
    "Hosur Road": "#4ECDC4",
    "ORR North 1": "#45B7D1",
    "Non-corridor": "#95A5A6",
}


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    """Load and preprocess the events CSV with all derived columns."""
    try:
        df = pd.read_csv(DATA_PATH, low_memory=False)
    except FileNotFoundError:
        st.error(
            "⚠️ **events.csv not found.** Please place your events.csv file in the `data/` folder and restart the app."
        )
        st.stop()

    # --- Parse datetimes ---
    for col in ["start_datetime", "end_datetime", "resolved_datetime", "closed_datetime", "modified_datetime", "created_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

    # --- Derived columns ---
    df["end_time"] = df["resolved_datetime"].where(
        df["resolved_datetime"].notna(), df["closed_datetime"]
    )

    df["duration_mins"] = (
        (df["end_time"] - df["start_datetime"]).dt.total_seconds() / 60
    )
    # Remove negative durations
    df.loc[df["duration_mins"] < 0, "duration_mins"] = np.nan

    df["hour"] = df["start_datetime"].dt.hour
    df["day_of_week"] = df["start_datetime"].dt.day_name()
    df["month"] = df["start_datetime"].dt.to_period("M").astype(str)
    df["is_peak_hour"] = df["hour"].apply(
        lambda h: 1 if pd.notna(h) and int(h) in PEAK_HOURS else 0
    )
    df["duration_hrs"] = df["duration_mins"] / 60

    # Clean up boolean column
    if "requires_road_closure" in df.columns:
        df["requires_road_closure"] = df["requires_road_closure"].astype(str).str.lower().isin(["true", "1", "yes"])

    # Normalize text columns
    for col in ["event_type", "event_cause", "status", "priority", "corridor", "zone", "junction"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace("nan", np.nan)

    # Fill corridor NaN
    df["corridor"] = df["corridor"].fillna("Non-corridor")
    df["zone"] = df["zone"].fillna("Unknown Zone")
    df["event_cause"] = df["event_cause"].fillna("others")
    df["event_type"] = df["event_type"].fillna("unplanned")
    df["status"] = df["status"].fillna("unknown")
    df["priority"] = df["priority"].fillna("Low")

    return df


@st.cache_data(ttl=3600)
def get_summary_stats(df: pd.DataFrame) -> dict:
    """Compute top-level summary statistics."""
    total = len(df)
    active = int((df["status"] == "active").sum())
    road_closures = int(df["requires_road_closure"].sum())
    high_priority = int((df["priority"] == "High").sum())

    date_min = df["start_datetime"].min()
    date_max = df["start_datetime"].max()

    return {
        "total_events": total,
        "active_events": active,
        "road_closures": road_closures,
        "high_priority": high_priority,
        "date_min": date_min,
        "date_max": date_max,
    }


@st.cache_data(ttl=3600)
def get_corridor_list(df: pd.DataFrame) -> list:
    corridors = df["corridor"].dropna().unique().tolist()
    corridors = sorted([c for c in corridors if c not in ["nan", "None", ""]])
    return corridors


@st.cache_data(ttl=3600)
def get_cause_list(df: pd.DataFrame) -> list:
    causes = df["event_cause"].dropna().unique().tolist()
    causes = sorted([c for c in causes if c not in ["nan", "None", ""]])
    return causes


@st.cache_data(ttl=3600)
def get_zone_list(df: pd.DataFrame) -> list:
    zones = df["zone"].dropna().unique().tolist()
    zones = sorted([z for z in zones if z not in ["nan", "None", "", "Unknown Zone"]])
    return zones
