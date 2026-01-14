from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from .utils import fmt_currency, fmt_pct


def export_board_pdf(output_path: Path, title: str, kpis: dict, mom: dict | None, sheet22_ctx: dict) -> Path:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)

    story = []
    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph("Overview - Financial Performance and NBIP Utilisation", styles["Normal"]))
    story.append(Spacer(1, 12))

    # KPI Table
    zero_names = ", ".join(kpis.get("zero_revenue_locations") or [])
    rows = [
        ["KPI", "Value"],
        ["Total SINBIP Revenue", fmt_currency(kpis["total_revenue"])],
        ["Avg Revenue per NBIP Location", fmt_currency(kpis["avg_revenue"])],
        ["Mobile Data Share", fmt_pct(kpis["data_share_pct"])],
        ["Mobile Voice Share", fmt_pct(kpis["voice_share_pct"])],
        ["Mobile SMS Share", fmt_pct(kpis["sms_share_pct"])],
        ["Zero-Revenue NBIP Sites", zero_names or "None"],
        ["Top Performing NBIP Site", f'{kpis["top_site"]} ({fmt_currency(kpis["top_site_value"])})'],
    ]

    if mom:
        delta_str = fmt_currency(mom["delta"])
        rows.append(["MoM Revenue Change", f'{delta_str} ({mom["pct_change"]:.1f}%)'])

    if sheet22_ctx.get("target_total") is not None:
        target = float(sheet22_ctx["target_total"])
        achievement = (kpis["total_revenue"] / target * 100.0) if target else 0.0
        rows.append(["Target Achievement (Sheet22)", f"{achievement:.1f}%"])

    table = Table(rows, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 14))

    # Executive Observations (board-safe)
    story.append(Paragraph("Executive Observations & Recommended Actions", styles["Heading2"]))
    story.append(Spacer(1, 6))

    concentration_pct = kpis["concentration_ratio"] * 100.0
    story.append(Paragraph(
        f"- Revenue is concentrated: the top 10 NBIP sites contribute {concentration_pct:.1f}% of total revenue.",
        styles["Normal"],
    ))
    story.append(Paragraph(
        f"- Underutilised assets: {kpis['zero_revenue_sites']} NBIP locations recorded zero revenue in the month.",
        styles["Normal"],
    ))
    story.append(Paragraph(
        "- Recommendation: Direct management to investigate zero-revenue sites and prioritise data-led service expansion.",
        styles["Normal"],
    ))

    if sheet22_ctx.get("control_total") is not None:
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Control Note (Sheet22): A control total was detected and can be used for internal reconciliation.",
            styles["Italic"],
        ))

    doc.build(story)
    return output_path
