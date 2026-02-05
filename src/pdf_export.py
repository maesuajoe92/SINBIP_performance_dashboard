from pathlib import Path

from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate

from utils import fmt_currency, fmt_pct


def _plot_revenue_mix(kpis: dict) -> Drawing:
    mix = kpis.get("revenue_mix", {})
    values = [mix.get("voice", 0), mix.get("sms", 0), mix.get("data", 0)]
    labels = ["Voice", "SMS", "Data"]
    total = sum(values) or 1
    drawing = Drawing(420, 230)
    pie = Pie()
    pie.x = 130
    pie.y = 10
    pie.width = 180
    pie.height = 180
    pie.data = values
    pie.labels = [f"{name} {v/total*100:.0f}%" for name, v in zip(labels, values)]
    pie.slices.strokeWidth = 0.5
    drawing.add(pie)
    drawing.add(String(0, 210, "Revenue Mix", fontSize=12))
    return drawing


def _plot_top_sites(df, title: str) -> Drawing:
    data = df.copy()
    drawing = Drawing(460, 260)
    chart = HorizontalBarChart()
    chart.x = 30
    chart.y = 20
    chart.height = 200
    chart.width = 380
    chart.data = [data["Total"].tolist()]
    chart.categoryAxis.categoryNames = data["Location"].tolist()
    chart.bars[0].fillColor = colors.HexColor("#4b9bb1")
    chart.valueAxis.valueMin = 0
    drawing.add(chart)
    drawing.add(String(0, 238, title, fontSize=12))
    return drawing


def _plot_trend(trend: dict) -> Drawing:
    months = trend.get("months", [])
    totals = trend.get("total_revenue", [])
    points = list(zip(range(len(months)), totals))
    drawing = Drawing(460, 240)
    chart = LinePlot()
    chart.x = 30
    chart.y = 25
    chart.height = 170
    chart.width = 380
    chart.data = [points]
    chart.lines[0].strokeColor = colors.HexColor("#7bd6d1")
    chart.xValueAxis.valueMin = 0
    chart.xValueAxis.valueMax = max(len(months) - 1, 0)
    chart.xValueAxis.valueSteps = list(range(len(months)))
    chart.xValueAxis.labelTextFormat = lambda v: months[int(v)] if months else ""
    chart.yValueAxis.valueMin = 0
    drawing.add(chart)
    drawing.add(String(0, 218, "Total Revenue Trend", fontSize=12))
    return drawing


def export_board_pdf(
    output_path: Path,
    title: str,
    kpis: dict,
    mom: dict | None,
    sheet22_ctx: dict,
    trend: dict | None = None,
    latest_name: str | None = None,
) -> Path:
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

    # Charts & tables (board-ready)
    story.append(Paragraph("Performance Highlights (Charts)", styles["Heading2"]))
    story.append(Spacer(1, 8))

    try:
        story.append(Paragraph(
            f"Revenue mix shows how voice, SMS and data contribute to total revenue"
            f"{f' in {latest_name}' if latest_name else ''}.",
            styles["Normal"],
        ))
        story.append(_plot_revenue_mix(kpis))
        story.append(Spacer(1, 10))
    except Exception:
        story.append(Paragraph("Revenue mix chart unavailable.", styles["Italic"]))

    top_10 = kpis.get("top_10_sites")
    if top_10 is not None and not top_10.empty:
        concentration_pct = kpis.get("concentration_ratio", 0) * 100.0
        story.append(Paragraph(
            f"Top 10 sites contribute {concentration_pct:.1f}% of total revenue, highlighting concentration risk.",
            styles["Normal"],
        ))
        try:
            story.append(_plot_top_sites(top_10, "Top 10 Locations by Revenue"))
        except Exception:
            story.append(Paragraph("Top 10 bar chart unavailable.", styles["Italic"]))
        story.append(Spacer(1, 8))
    bottom_10 = kpis.get("bottom_10_sites")
    if bottom_10 is not None and not bottom_10.empty:
        zero_count = kpis.get("zero_revenue_sites", 0)
        story.append(Paragraph(
            f"Bottom 10 locations identify underperforming sites; {zero_count} locations recorded zero revenue.",
            styles["Normal"],
        ))
        try:
            story.append(_plot_top_sites(bottom_10, "Bottom 10 Locations by Revenue"))
        except Exception:
            story.append(Paragraph("Bottom 10 bar chart unavailable.", styles["Italic"]))
        story.append(Spacer(1, 8))

    if trend:
        latest_total = trend["total_revenue"][-1] if trend["total_revenue"] else 0.0
        mom_line = ""
        if mom:
            mom_line = f" MoM change: {fmt_currency(mom['delta'])} ({mom['pct_change']:.1f}%)."
        story.append(Paragraph(
            f"Total revenue trend shows month-to-month movement; latest month total is {fmt_currency(latest_total)}."
            f"{mom_line}",
            styles["Normal"],
        ))
        try:
            story.append(_plot_trend(trend))
        except Exception:
            story.append(Paragraph("Trend chart unavailable.", styles["Italic"]))
        story.append(Spacer(1, 12))

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
