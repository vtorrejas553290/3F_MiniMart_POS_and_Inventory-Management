# ─────────────────────────────────────────────
# INVENTORY REPORT — data builder + PDF export
# ─────────────────────────────────────────────

import os
from datetime import datetime
from tkinter import filedialog

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from database import get_connection, now_local


# ─────────────────────────────────────────────
# FONT REGISTRATION (for ₱)
# ─────────────────────────────────────────────

FONT_REGULAR = "Helvetica"
FONT_BOLD    = "Helvetica-Bold"
FONT_ITALIC  = "Helvetica-Oblique"

def _register_fonts():
    global FONT_REGULAR, FONT_BOLD, FONT_ITALIC
    try:
        import reportlab
        fonts_dir = os.path.join(os.path.dirname(reportlab.__file__), "fonts")

        regular = os.path.join(fonts_dir, "DejaVuSans.ttf")
        bold    = os.path.join(fonts_dir, "DejaVuSans-Bold.ttf")
        italic  = os.path.join(fonts_dir, "DejaVuSans-Oblique.ttf")

        if os.path.exists(regular):
            pdfmetrics.registerFont(TTFont("DejaVu", regular))
            FONT_REGULAR = "DejaVu"
        if os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold))
            FONT_BOLD = "DejaVu-Bold"
        if os.path.exists(italic):
            pdfmetrics.registerFont(TTFont("DejaVu-Italic", italic))
            FONT_ITALIC = "DejaVu-Italic"
    except Exception:
        pass


_register_fonts()


# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────

BRAND_GREEN = colors.HexColor("#22A647")
BRAND_BLUE  = colors.HexColor("#3B6FD4")
FG_PRIMARY  = colors.HexColor("#0F172A")
FG_MUTED    = colors.HexColor("#64748B")
BORDER_GREY = colors.HexColor("#E2E8F0")
ROW_ALT     = colors.HexColor("#F8FAFC")
CAT_BG      = colors.HexColor("#EAF0FF")
SUB_BG      = colors.HexColor("#F1F5F9")
DANGER      = colors.HexColor("#DC2626")
AMBER       = colors.HexColor("#D97706")
SUCCESS     = colors.HexColor("#16A34A")


# ─────────────────────────────────────────────
# DATA BUILDER
# ─────────────────────────────────────────────

def build_inventory_report_data(products, filters, exporter_name=""):
    date_from = filters.get("date_from") or None
    date_to   = filters.get("date_to")   or None

    enriched = []
    for p in products:
        pid = p["product_id"]

        remaining = p.get("stock_qty", 0) or 0
        stock_in  = _stock_in_for_product(pid, date_from, date_to)
        stock_out = _stock_out_for_product(pid, date_from, date_to)
        initial   = remaining - stock_in + stock_out

        low_level = p.get("low_stock_level", 0) or 0
        if remaining <= 0:
            status, status_color = "Out", "danger"
        elif remaining <= low_level:
            status, status_color = "Low", "amber"
        else:
            status, status_color = "OK", "ok"

        enriched.append({
            "product_id":   pid,
            "name":         _display_name(p),
            "category":     p.get("category_name") or "-",
            "unit":         p.get("unit") or "pc",
            "initial":      initial,
            "stock_in":     stock_in,
            "stock_out":    stock_out,
            "remaining":    remaining,
            "status":       status,
            "status_color": status_color,
        })

    # ---- Group by category ----
    groups_map = {}
    for e in enriched:
        groups_map.setdefault(e["category"], []).append(e)

    groups = []
    for cat in sorted(groups_map.keys()):
        rows = sorted(groups_map[cat], key=lambda r: r["name"])
        subtotal = {
            "initial":   sum(r["initial"]   for r in rows),
            "stock_in":  sum(r["stock_in"]  for r in rows),
            "stock_out": sum(r["stock_out"] for r in rows),
            "remaining": sum(r["remaining"] for r in rows),
        }
        groups.append({
            "category": cat,
            "rows":     rows,
            "subtotal": subtotal,
        })

    summary = {
        "total_products": len(enriched),
        "initial":        sum(r["initial"]   for r in enriched),
        "stock_in":       sum(r["stock_in"]  for r in enriched),
        "stock_out":      sum(r["stock_out"] for r in enriched),
        "remaining":      sum(r["remaining"] for r in enriched),
        "low_count":      sum(1 for r in enriched if r["status"] == "Low"),
        "out_count":      sum(1 for r in enriched if r["status"] == "Out"),
    }

    return {
        "generated_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filters":       filters,
        "summary":       summary,
        "groups":        groups,
        "exporter_name": exporter_name,
    }


# ─────────────────────────────────────────────
# DB QUERIES
# ─────────────────────────────────────────────

def _stock_in_for_product(product_id, date_from, date_to):
    conn = get_connection()
    sql = """
        SELECT COALESCE(SUM(quantity), 0) AS total
        FROM batches
        WHERE product_id = ?
          AND is_archived = 0
    """
    params = [product_id]
    if date_from:
        sql += " AND DATE(received_at) >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND DATE(received_at) <= ?"
        params.append(date_to)

    row = conn.execute(sql, params).fetchone()
    conn.close()
    return row["total"] if row else 0


def _stock_out_for_product(product_id, date_from, date_to):
    conn = get_connection()
    sql = """
        SELECT COALESCE(SUM(ti.quantity), 0) AS total
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.transaction_id
        WHERE ti.product_id = ?
    """
    params = [product_id]
    if date_from:
        sql += " AND DATE(t.created_at) >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND DATE(t.created_at) <= ?"
        params.append(date_to)

    row = conn.execute(sql, params).fetchone()
    conn.close()
    return row["total"] if row else 0


def _display_name(p):
    parts = [p.get("brand"), p.get("name"), p.get("size")]
    return " ".join(part for part in parts if part)


# ─────────────────────────────────────────────
# TEXT RENDERING (preview)
# ─────────────────────────────────────────────

def render_inventory_report_text(data):
    W = 96

    lines = []

    def line(t=""):
        lines.append(t)

    def hr(ch="="):
        return ch * W

    # ---- Header ----
    line(hr("="))
    line("3F MiniMart".center(W))
    line("Inventory Movement Report".center(W))
    line(f"Snapshot: {data['generated_at']}".center(W))
    if data.get("filters"):
        line(_filter_summary_line(data["filters"]).center(W))
    line(hr("="))

    # ---- Summary ----
    s = data["summary"]
    line("SUMMARY")
    line("-" * W)
    line(f"  Total Products    : {s['total_products']:>6}")
    line(f"  Initial Stock     : {s['initial']:>6}")
    line(f"  Stock-In          : {s['stock_in']:>6}")
    line(f"  Stock-Out         : {s['stock_out']:>6}")
    line(f"  Remaining Stock   : {s['remaining']:>6}")
    line()
    line(f"  Low Stock: {s['low_count']}      Out of Stock: {s['out_count']}")
    line(hr("="))

    # ---- Products ----
    line("PRODUCTS")
    line()

    col_w = {
        "name":      36,
        "unit":       5,
        "initial":    9,
        "in":         9,
        "out":        9,
        "remaining":  10,
        "status":     6,
    }

    header = (
        "Name".ljust(col_w["name"]) + " " +
        "Unit".center(col_w["unit"]) + " " +
        "Initial".rjust(col_w["initial"]) + " " +
        "In".rjust(col_w["in"]) + " " +
        "Out".rjust(col_w["out"]) + " " +
        "Remaining".rjust(col_w["remaining"]) + " " +
        "Status".center(col_w["status"])
    )
    line(header)
    line("-" * len(header))

    for group in data["groups"]:
        line(f"[{group['category'].upper()}]  ({len(group['rows'])} products)")

        for r in group["rows"]:
            name = r["name"][:col_w["name"]].ljust(col_w["name"])
            unit = (r["unit"][:col_w["unit"]]).center(col_w["unit"])
            row = (
                name + " " +
                unit + " " +
                f"{r['initial']:>7}".rjust(col_w["initial"]) + " " +
                f"{r['stock_in']:>7}".rjust(col_w["in"]) + " " +
                f"{r['stock_out']:>7}".rjust(col_w["out"]) + " " +
                f"{r['remaining']:>8}".rjust(col_w["remaining"]) + " " +
                r["status"].center(col_w["status"])
            )
            line("  " + row)

        sub = group["subtotal"]
        line(
            f"  Subtotal: initial {sub['initial']}  •  "
            f"in {sub['stock_in']}  •  out {sub['stock_out']}  •  "
            f"remaining {sub['remaining']}"
        )
        line()

    # ---- Footer ----
    line(hr("="))
    line(f"Exported by: {data.get('exporter_name') or '-'}".center(W))
    line(f"Exported on: {data['generated_at']}".center(W))
    line(hr("="))

    return "\n".join(lines)


def _filter_summary_line(filters):
    parts = []
    if filters.get("product_id"):
        parts.append("Specific product")
    if filters.get("category"):
        parts.append(f"Category: {filters['category']}")
    df = filters.get("date_from")
    dt = filters.get("date_to")
    if df and dt and df == dt:
        parts.append(f"Date: {df}")
    elif df and dt:
        parts.append(f"{df} → {dt}")
    elif df:
        parts.append(f"From {df}")
    elif dt:
        parts.append(f"Until {dt}")
    else:
        parts.append("All time")
    if filters.get("low_only"):
        parts.append("Low stock only")
    if filters.get("show_archived"):
        parts.append("Incl. archived")
    return "  •  ".join(parts)


# ─────────────────────────────────────────────
# PDF EXPORT
# ─────────────────────────────────────────────

def export_inventory_pdf(data, parent_window=None):
    default_name = _default_filename()
    path = filedialog.asksaveasfilename(
        title="Save Inventory Report",
        defaultextension=".pdf",
        initialfile=default_name,
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        parent=parent_window,
    )
    if not path:
        return False, "Cancelled."

    try:
        _build_pdf(path, data)
        return True, path
    except Exception as e:
        return False, str(e)


def _default_filename():
    today = datetime.now().strftime("%Y%m%d")
    return f"3F_Inventory_{today}.pdf"


def _build_pdf(path, data):
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="3F MiniMart — Inventory Movement Report",
        author="3F MiniMart POS",
    )

    styles = _make_styles()
    story = []

    # ---- Header ----
    story.append(Paragraph("3F MiniMart", styles["3f_brand"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Inventory Movement Report", styles["3f_title"]))
    story.append(Spacer(1, 4))
    subtitle = f"Snapshot: {data['generated_at']}"
    if data.get("filters"):
        subtitle += "  •  " + _filter_summary_line(data["filters"])
    story.append(Paragraph(subtitle, styles["3f_subtitle"]))
    story.append(Spacer(1, 18))

    # ---- Summary ----
    story.append(Paragraph("Summary", styles["3f_section"]))
    story.append(Spacer(1, 6))

    s = data["summary"]
    summary_data = [
        ["Total Products", f"{s['total_products']:,}",
         "Initial Stock", f"{s['initial']:,}"],
        ["Stock-In", f"{s['stock_in']:,}",
         "Stock-Out", f"{s['stock_out']:,}"],
        ["Remaining Stock", f"{s['remaining']:,}",
         "Low / Out", f"{s['low_count']} / {s['out_count']}"],
    ]
    summary_table = Table(summary_data,
                          colWidths=[1.3 * inch, 1.4 * inch,
                                     1.3 * inch, 1.4 * inch])
    summary_table.setStyle(TableStyle([
        ("FONT",         (0, 0), (0, -1), FONT_BOLD, 9),
        ("FONT",         (2, 0), (2, -1), FONT_BOLD, 9),
        ("FONT",         (1, 0), (1, -1), FONT_BOLD, 13),
        ("FONT",         (3, 0), (3, -1), FONT_BOLD, 13),
        ("TEXTCOLOR",    (0, 0), (0, -1), FG_MUTED),
        ("TEXTCOLOR",    (2, 0), (2, -1), FG_MUTED),
        ("TEXTCOLOR",    (1, 0), (1, -1), BRAND_BLUE),
        ("TEXTCOLOR",    (3, 0), (3, -1), FG_PRIMARY),
        ("BACKGROUND",   (0, 0), (-1, -1), ROW_ALT),
        ("BOX",          (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("INNERGRID",    (0, 0), (-1, -1), 0.25, BORDER_GREY),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # ---- Products table ----
    story.append(Paragraph("Products by Category", styles["3f_section"]))
    story.append(Spacer(1, 6))

    col_widths = [
        3.30 * inch,   # Name
        0.45 * inch,   # Unit
        0.75 * inch,   # Initial
        0.65 * inch,   # Stock-In
        0.70 * inch,   # Stock-Out
        0.85 * inch,   # Remaining
        0.55 * inch,   # Status
    ]

    header = ["Name", "Unit", "Initial", "In", "Out", "Remaining", "Status"]
    rows = [header]
    style_cmds = [
        ("BACKGROUND",   (0, 0), (-1, 0), BRAND_BLUE),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONT",         (0, 0), (-1, 0), FONT_BOLD, 9),
        ("ALIGN",        (0, 0), (0, -1), "LEFT"),
        ("ALIGN",        (1, 0), (1, -1), "CENTER"),
        ("ALIGN",        (2, 0), (6, -1), "RIGHT"),
        ("FONT",         (0, 1), (-1, -1), FONT_REGULAR, 9),
        ("TEXTCOLOR",    (0, 1), (-1, -1), FG_PRIMARY),
        ("LINEBELOW",    (0, 0), (-1, 0), 0.5, BRAND_BLUE),
        ("LINEBELOW",    (0, 1), (-1, -1), 0.25, BORDER_GREY),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]

    r = 1
    for group in data["groups"]:
        rows.append([f"[{group['category'].upper()}]  "
                     f"({len(group['rows'])} products)",
                     "", "", "", "", "", ""])
        style_cmds.append(("SPAN", (0, r), (-1, r)))
        style_cmds.append(("BACKGROUND", (0, r), (-1, r), CAT_BG))
        style_cmds.append(("FONT", (0, r), (-1, r), FONT_BOLD, 9))
        style_cmds.append(("TEXTCOLOR", (0, r), (-1, r), BRAND_BLUE))
        r += 1

        for item in group["rows"]:
            rows.append([
                item["name"],
                item["unit"],
                f"{item['initial']:,}",
                f"{item['stock_in']:,}",
                f"{item['stock_out']:,}",
                f"{item['remaining']:,}",
                item["status"],
            ])
            color = {
                "danger": DANGER,
                "amber":  AMBER,
                "ok":     SUCCESS,
            }.get(item["status_color"], FG_PRIMARY)
            style_cmds.append(("TEXTCOLOR", (6, r), (6, r), color))
            style_cmds.append(("FONT", (6, r), (6, r), FONT_BOLD, 9))
            r += 1

        sub = group["subtotal"]
        rows.append([
            "Subtotal",
            "",
            f"{sub['initial']:,}",
            f"{sub['stock_in']:,}",
            f"{sub['stock_out']:,}",
            f"{sub['remaining']:,}",
            "",
        ])
        style_cmds.append(("SPAN", (0, r), (1, r)))
        style_cmds.append(("BACKGROUND", (0, r), (-1, r), SUB_BG))
        style_cmds.append(("FONT", (0, r), (-1, r), FONT_BOLD, 9))
        style_cmds.append(("ALIGN", (0, r), (0, r), "RIGHT"))
        r += 1

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    # ---- Footer ----
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"Exported by: {data.get('exporter_name') or '-'}",
        styles["3f_footnote"],
    ))
    story.append(Paragraph(
        f"Exported on: {data['generated_at']}",
        styles["3f_footnote"],
    ))

    doc.build(story)


# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────

def _make_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="3f_brand", parent=styles["Normal"],
        fontName=FONT_BOLD, fontSize=22, leading=26,
        textColor=BRAND_GREEN, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="3f_title", parent=styles["Normal"],
        fontName=FONT_BOLD, fontSize=15, leading=18,
        textColor=FG_PRIMARY, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="3f_subtitle", parent=styles["Normal"],
        fontName=FONT_REGULAR, fontSize=9, leading=12,
        textColor=FG_MUTED, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="3f_section", parent=styles["Normal"],
        fontName=FONT_BOLD, fontSize=12, leading=15,
        textColor=FG_PRIMARY, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="3f_footnote", parent=styles["Normal"],
        fontName=FONT_ITALIC, fontSize=8, leading=11,
        textColor=FG_MUTED, alignment=TA_LEFT,
    ))

    return styles