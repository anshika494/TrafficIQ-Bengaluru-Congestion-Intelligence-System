"""
risk_model.py — Formula-driven risk scoring and resolution time prediction.
Works entirely without CSV data (form-based inputs only).
"""

# --- Cause weights ---
CAUSE_WEIGHTS = {
    "accident": 25,
    "public_event": 22,
    "protest": 20,
    "vip_movement": 18,
    "construction": 18,
    "water_logging": 15,
    "procession": 15,
    "congestion": 12,
    "vehicle_breakdown": 10,
    "pot_holes": 8,
    "tree_fall": 8,
    "road_conditions": 8,
    "others": 5,
}

# --- Corridor weights ---
CORRIDOR_WEIGHTS = {
    "Mysore Road": 12,
    "Bellary Road 1": 10,
    "ORR North 1": 10,
    "ORR East 1": 9,
    "Old Madras Road": 8,
    "Hosur Road": 8,
    "Bannerghata Road": 7,
    "Tumkur Road": 6,
    "Bellary Road 2": 6,
    "Magadi Road": 5,
    "Non-corridor": 3,
}

# --- Peak hours ---
PEAK_HOURS = {20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6}

# --- High-traffic days ---
HIGH_TRAFFIC_DAYS = {"Thursday", "Friday", "Saturday"}

# --- Median resolution times (in minutes) per cause ---
MEDIAN_RESOLUTION_MINS = {
    "accident": 48,
    "vehicle_breakdown": 50,
    "procession": 55,
    "congestion": 75,
    "vip_movement": 90,
    "public_event": 120,
    "protest": 150,
    "tree_fall": 180,
    "water_logging": 480,
    "construction": 13662,
    "road_conditions": 25888,
    "pot_holes": 35185,
    "others": 200,
}

# --- Barricade points per corridor ---
BARRICADE_POINTS = {
    "Mysore Road": [
        "Mysore Road Junction @ Chord Road",
        "Kengeri Satellite Town Intersection",
        "Rajarajeshwari Nagar Signal",
    ],
    "Bellary Road 1": [
        "Hebbal Flyover Junction",
        "Mekhri Circle",
        "Sankey Road Intersection",
    ],
    "Bellary Road 2": [
        "Yelhanka Junction",
        "Kogilu Cross",
        "Kattigenahalli Circle",
    ],
    "Tumkur Road": [
        "Yeswanthpur Circle",
        "Nagasandra Metro Junction",
        "Peenya Industrial Area Signal",
    ],
    "Hosur Road": [
        "Silk Board Junction",
        "Electronic City Flyover",
        "Bommanahalli Signal",
    ],
    "ORR North 1": [
        "Hebbal ORR Ramp",
        "Nagawara Junction",
        "Thanisandra Signal",
    ],
    "ORR East 1": [
        "KR Puram ORR",
        "Marathahalli Bridge",
        "Sarjapur Road ORR Junction",
    ],
    "Old Madras Road": [
        "KR Puram Bridge",
        "Banaswadi Signal",
        "Hoodi Junction",
    ],
    "Magadi Road": [
        "Rajajinagar Industrial Estate",
        "Chord Road Junction",
        "Mysore Road Divergence",
    ],
    "Bannerghatta Road": [
        "Jayadeva Hospital Junction",
        "JP Nagar Signal",
        "Gottigere ORR Junction",
    ],
    "Non-corridor": [
        "Nearest Major Signal",
        "Local Junction",
    ],
}

# --- Diversion routes per corridor ---
DIVERSION_ROUTES = {
    "Mysore Road": [
        "→ Via Chord Road → Magadi Road → Rajajinagar",
        "→ Via Kanakapura Road → NICE Road Connector",
    ],
    "Bellary Road 1": [
        "→ Via Outer Ring Road (North) → Hebbal",
        "→ Via Sadahalli Gate → Old Airport Road",
    ],
    "Bellary Road 2": [
        "→ Via Doddaballapur Road → NH44",
        "→ Via Kogilu Main Road → ORR North",
    ],
    "Tumkur Road": [
        "→ Via Magadi Road → Ring Road",
        "→ Via Peenya Industrial Road → ORR",
    ],
    "Hosur Road": [
        "→ Via NICE Road → Kanakapura Road",
        "→ Via Sarjapur Road → ORR East",
    ],
    "ORR North 1": [
        "→ Via Bellary Road → Mekhri Circle",
        "→ Via Thanisandra Main Road",
    ],
    "ORR East 1": [
        "→ Via Whitefield Road → Hoodi Junction",
        "→ Via Old Madras Road → KR Puram",
    ],
    "Old Madras Road": [
        "→ Via Outer Ring Road → Banaswadi",
        "→ Via HAL Airport Road",
    ],
    "Magadi Road": [
        "→ Via Mysore Road → Chord Road",
        "→ Via Rajajinagar → Ring Road",
    ],
    "Bannerghatta Road": [
        "→ Via NICE Road → Hosur Road",
        "→ Via Kanakapura Road",
    ],
    "Non-corridor": [
        "→ Via nearest parallel arterial road",
        "→ Via alternate local route",
    ],
}


def compute_risk_score(
    corridor: str,
    event_cause: str,
    day_of_week: str,
    hour: int,
    event_type: str,
    requires_road_closure: bool,
    duration_hrs: float = 1.0,
) -> dict:
    """
    Compute risk score (0–100) using the weighted formula.
    Returns dict with score, label, color, and component breakdown.
    """
    base = 30
    peak_bonus = 25 if hour in PEAK_HOURS else 0
    day_bonus = 10 if day_of_week in HIGH_TRAFFIC_DAYS else 0
    cause_bonus = CAUSE_WEIGHTS.get(event_cause, 5)
    closure_bonus = 20 if requires_road_closure else 0
    type_bonus = 10 if event_type.lower() == "unplanned" else 0
    corridor_bonus = CORRIDOR_WEIGHTS.get(corridor, 4)

    raw_score = base + peak_bonus + day_bonus + cause_bonus + closure_bonus + type_bonus + corridor_bonus
    score = max(0, min(100, raw_score))

    if score < 40:
        label = "LOW"
        color = "#27AE60"
        bar_color = "normal"
    elif score < 70:
        label = "MODERATE"
        color = "#F39C12"
        bar_color = "off"
    elif score < 85:
        label = "HIGH"
        color = "#E67E22"
        bar_color = "off"
    else:
        label = "CRITICAL"
        color = "#E24B4A"
        bar_color = "inverse"

    breakdown = {
        "Base Score": base,
        "Peak Hour Bonus": peak_bonus,
        "High-Traffic Day Bonus": day_bonus,
        "Cause Weight": cause_bonus,
        "Road Closure Bonus": closure_bonus,
        "Unplanned Event Bonus": type_bonus,
        "Corridor Risk Weight": corridor_bonus,
    }

    return {
        "score": score,
        "label": label,
        "color": color,
        "bar_color": bar_color,
        "breakdown": breakdown,
        "is_peak": hour in PEAK_HOURS,
    }


def predict_resolution_time(
    event_cause: str,
    is_peak_hour: bool,
    requires_road_closure: bool,
    event_type: str,
) -> dict:
    """
    Predict resolution time based on cause and modifying factors.
    Returns dict with minutes, hours, and formatted string.
    """
    base_mins = MEDIAN_RESOLUTION_MINS.get(event_cause, 200)

    multiplier = 1.0
    if is_peak_hour:
        multiplier *= 1.3
    if requires_road_closure:
        multiplier *= 1.2
    if event_type.lower() == "planned":
        multiplier *= 0.9

    total_mins = base_mins * multiplier
    hours = int(total_mins // 60)
    minutes = int(total_mins % 60)

    if hours >= 24:
        days = hours // 24
        rem_hrs = hours % 24
        formatted = f"{days}d {rem_hrs}h {minutes}m"
    elif hours > 0:
        formatted = f"{hours}h {minutes}m"
    else:
        formatted = f"{minutes} minutes"

    return {
        "total_mins": total_mins,
        "total_hrs": total_mins / 60,
        "hours": hours,
        "minutes": minutes,
        "formatted": formatted,
    }


def generate_deployment_recommendation(
    corridor: str,
    event_cause: str,
    risk_score: int,
    is_peak_hour: bool,
    requires_road_closure: bool,
) -> dict:
    """Generate AI deployment recommendation based on risk inputs."""
    # Personnel
    base_personnel = 4
    if risk_score > 70:
        base_personnel += 6
    elif risk_score > 40:
        base_personnel += 4
    if requires_road_closure:
        base_personnel += 3
    if is_peak_hour:
        base_personnel += 2

    # Barricade points
    barricades = BARRICADE_POINTS.get(corridor, BARRICADE_POINTS["Non-corridor"])

    # Diversion routes
    diversions = DIVERSION_ROUTES.get(corridor, DIVERSION_ROUTES["Non-corridor"])

    # Alert zone radius
    alert_radius_km = max(1, min(8, risk_score // 10))

    # Special flags
    flags = []
    if event_cause == "accident":
        flags.append("🚑 Ambulance route clearance needed")
    if event_cause == "vip_movement":
        flags.append("🎖️ VIP protocol required — coordinate with security detail")
    if event_cause in ["public_event", "protest"]:
        flags.append("📺 Media coordination needed")
    if event_cause in ["pot_holes", "road_conditions", "water_logging", "construction"]:
        flags.append("🔧 PWD notification required")
    if is_peak_hour:
        flags.append("⏰ Peak hour deployment — increase visibility at intersections")
    if requires_road_closure:
        flags.append("🚧 Road closure signage and advance warning required")

    return {
        "personnel": base_personnel,
        "barricades": barricades,
        "diversions": diversions,
        "alert_radius_km": alert_radius_km,
        "flags": flags,
    }
