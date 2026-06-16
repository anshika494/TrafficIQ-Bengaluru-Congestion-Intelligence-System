"""
pdf_export.py — PDF generation for deployment plans using fpdf2.
"""

from fpdf import FPDF
from datetime import datetime
import io


class TrafficIQPDF(FPDF):
    """Custom PDF class with header/footer branding."""

    def normalize_text(self, text):
        if not isinstance(text, str):
            text = str(text)
        
        # Replace common unsupported characters with ASCII counterparts
        replacements = {
            "—": "-",   # em-dash
            "–": "-",   # en-dash
            "→": "->",  # right arrow
            "•": "-",   # bullet point
            "🏆": "[Top]",
            "⏳": "[Time]",
            "⏰": "[Peak]",
            "🚨": "[Alert]",
            "🚧": "[Closure]",
            "👮": "[Personnel]",
            "🔀": "[Diversion]",
            "🚌": "[BTMC]",
            "📺": "[Media]",
            "🎖️": "[VIP]",
            "🚑": "[Ambulance]",
            "📻": "[Radio]",
            "📱": "[Alert]",
            "✓": "*",
            "✔": "*",
            "✅": "[OK]",
            "⚠️": "[Warning]",
            "🔮": "[AI]",
            "⚡": "[Note]",
            "📍": "*",
        }
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)
            
        # Clean any remaining characters outside latin-1 to avoid fpdf encoding crash
        text = text.encode("latin-1", errors="replace").decode("latin-1")
        return super().normalize_text(text)

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_fill_color(15, 17, 23)
        self.set_text_color(226, 75, 74)
        self.cell(0, 12, "TrafficIQ - Bengaluru Congestion Intelligence", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(200, 200, 200)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, f"Generated: {datetime.now().strftime('%d %b %Y %H:%M IST')}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(226, 75, 74)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | Bengaluru Traffic Police - EDCI System", align="C")

    def section_title(self, title: str, color=(226, 75, 74)):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*color)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*color)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_text_color(30, 30, 30)
        self.ln(3)

    def key_value_row(self, key: str, value: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(65, 7, key + ":", border=0)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(20, 20, 20)
        self.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")

    def bullet_item(self, text: str, color=(60, 60, 60)):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*color)
        self.cell(8, 7, "-")
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")

    def risk_badge(self, risk_score: int, risk_label: str):
        if risk_score >= 85:
            color = (226, 75, 74)
        elif risk_score >= 70:
            color = (230, 126, 34)
        elif risk_score >= 40:
            color = (243, 156, 18)
        else:
            color = (39, 174, 96)

        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 12)
        self.cell(
            0, 10,
            f"  RISK SCORE: {risk_score}/100 - {risk_label}  ",
            align="C", fill=True, new_x="LMARGIN", new_y="NEXT"
        )
        self.set_text_color(20, 20, 20)
        self.ln(4)


def generate_risk_forecaster_pdf(
    corridor: str,
    event_cause: str,
    day_of_week: str,
    hour: int,
    event_type: str,
    requires_road_closure: bool,
    risk_score: int,
    risk_label: str,
    resolution_formatted: str,
    personnel: int,
    barricades: list,
    diversions: list,
    alert_radius_km: float,
    flags: list,
) -> bytes:
    """Generate a PDF deployment plan for the Risk Forecaster page."""

    pdf = TrafficIQPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(10, 15, 10)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Risk Badge
    pdf.risk_badge(risk_score, risk_label)

    # Event Details
    pdf.section_title("EVENT DETAILS")
    pdf.key_value_row("Corridor", corridor)
    pdf.key_value_row("Event Cause", event_cause.replace("_", " ").title())
    pdf.key_value_row("Day of Week", day_of_week)
    pdf.key_value_row("Hour of Day", f"{hour:02d}:00")
    pdf.key_value_row("Event Type", event_type.title())
    pdf.key_value_row("Road Closure", "Yes" if requires_road_closure else "No")
    pdf.ln(4)

    # Resolution Time
    pdf.section_title("PREDICTED RESOLUTION TIME", color=(52, 152, 219))
    pdf.key_value_row("Estimated Duration", resolution_formatted)
    pdf.ln(4)

    # Deployment Recommendation
    pdf.section_title("DEPLOYMENT RECOMMENDATION", color=(39, 174, 96))
    pdf.key_value_row("Personnel Required", f"{personnel} officers")
    pdf.key_value_row("Alert Zone Radius", f"{alert_radius_km} km")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 7, "Barricade Points:", new_x="LMARGIN", new_y="NEXT")
    for b in barricades:
        pdf.bullet_item(b)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Diversion Routes:", new_x="LMARGIN", new_y="NEXT")
    for d in diversions:
        pdf.bullet_item(d)
    pdf.ln(2)

    if flags:
        pdf.section_title("SPECIAL FLAGS", color=(230, 126, 34))
        for f in flags:
            # Strip emoji for PDF compatibility
            clean_flag = f.encode("ascii", errors="ignore").decode("ascii").strip()
            if not clean_flag:
                clean_flag = f[2:] if len(f) > 2 else f
            pdf.bullet_item(clean_flag, color=(180, 80, 20))
    pdf.ln(4)

    # Footer note
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 6,
        "This deployment plan is generated by the TrafficIQ AI system based on "
        "historical Bengaluru traffic data (Nov 2023 - Apr 2024). Actual conditions "
        "may vary. Always consult senior officers for final deployment decisions.",
        align="C"
    )

    return bytes(pdf.output())


def generate_event_planner_pdf(
    event_name: str,
    event_type: str,
    location: str,
    corridor: str,
    crowd_size: str,
    event_date: str,
    start_time: str,
    end_time: str,
    risk_score: int,
    risk_label: str,
    personnel: int,
    vehicles: int,
    barricade_units: int,
    first_aid_posts: int,
    traffic_marshals: int,
    primary_diversions: list,
    secondary_diversion: str,
    btmc_required: bool,
    media_advisory: bool,
    vip_protocol: bool,
    ambulances: int,
) -> bytes:
    """Generate a PDF deployment plan for the Event Planner page."""

    pdf = TrafficIQPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(10, 15, 10)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Event Header
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, event_name, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, f"{location} | {event_date} | {start_time} - {end_time}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.risk_badge(risk_score, risk_label)

    # Resource Requirements
    pdf.section_title("RESOURCE REQUIREMENTS")
    pdf.key_value_row("Personnel (Officers)", str(personnel))
    pdf.key_value_row("Vehicles", str(vehicles))
    pdf.key_value_row("Barricade Units", str(barricade_units))
    pdf.key_value_row("First Aid Posts", str(first_aid_posts))
    pdf.key_value_row("Traffic Marshals", str(traffic_marshals))
    pdf.key_value_row("Crowd Category", crowd_size)
    pdf.key_value_row("Nearest Corridor", corridor)
    pdf.ln(4)

    # Deployment Timeline
    pdf.section_title("DEPLOYMENT TIMELINE", color=(52, 152, 219))
    timeline = [
        ("T-48h", "Route survey and dry run"),
        ("T-24h", "Barricade deployment briefing"),
        ("T-6h", "Personnel deployment begins"),
        ("T-2h", "Traffic diversion activated"),
        ("T-0", "Event begins - full deployment"),
        ("T+End", "Gradual withdrawal begins"),
        ("T+2h", "Full clearance target"),
    ]
    for t, desc in timeline:
        pdf.key_value_row(t, desc)
    pdf.ln(4)

    # Diversion Plan
    pdf.section_title("DIVERSION PLAN", color=(155, 89, 182))
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 7, "Primary Diversions:", new_x="LMARGIN", new_y="NEXT")
    for d in primary_diversions:
        pdf.bullet_item(d)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Secondary Diversion:", new_x="LMARGIN", new_y="NEXT")
    pdf.bullet_item(secondary_diversion)
    pdf.ln(4)

    # Communication Plan
    pdf.section_title("COMMUNICATION PLAN", color=(39, 174, 96))
    pdf.key_value_row("BTMC Coordination", "Required" if btmc_required else "Not Required")
    pdf.key_value_row("Media Advisory", "Required" if media_advisory else "Not Required")
    pdf.key_value_row("VIP Protocol Unit", "Required" if vip_protocol else "Not Required")
    pdf.key_value_row("Ambulances Pre-positioned", str(ambulances))
    pdf.ln(4)

    # Footer note
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 6,
        "This deployment plan is generated by the TrafficIQ AI system. "
        "Actual resource requirements may vary. Consult with event organizers "
        "and senior police officers before finalizing deployment.",
        align="C"
    )

    return bytes(pdf.output())
