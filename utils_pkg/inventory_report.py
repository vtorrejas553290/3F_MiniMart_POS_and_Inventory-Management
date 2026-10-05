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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
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

def build_inventory_report_data(products, filters=None):
    """
    Given a list of product rows (from InventoryController), build the
    structured report data used by both the preview and the PDF export.

    Returns:
        {
          "generated_at": str,
          "filters":      dict or None,
          "summary":      dict,
          "groups":       [ { "category": str,
                              "rows":     [ ... ],
                              "subtotal": { "qty": int,
                                            "value": float,
                                            "revenue": float } } ],
          "expiring":     [ { ... } ]
        }
    """
    today = datetime.now().date()

    # ---- Summary aggregates ----
    total_skus = len(products)
    total_units = 0
    total_value = 0.0
    total_revenue = 0.0
    low_count = 0
    out_count = 0

    # ---- Enrich every product with computed fields ----
    enriched = []
    for p in products:
        qty = p.get("stock_qty", 0) or 0
        price = p.get("price", 0) or 0
        cost = p.get("cost_price", 0) or 0

        # Stock value uses BATCH cost, not product cost.
        stock_value = _stock_value_from_batches(p["product_id"])
        potential_revenue = price * qty

        low_level = p.get("low_stock_level", 0) or 0
        if qty <= 0:
            status, status_color = "Out", "danger"
            out_count += 1
        elif qty <= low_level:
            status, status_color = "Low", "amber"
            low_count += 1
        else:
            status, status_color = "OK", "ok"

        # ---- Expiration flag ----
        exp = p.get("earliest_expiration")
        exp_days = None
        if exp:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                exp_days = (exp_date - today).days
            except ValueError:
                exp_days = None

        enriched.append({
            "product_id":        p["product_id"],
            "name":              _display_name(p),
            "category":          p.get("category_name") or "-",
            "unit":              p.get("unit") or "pc",
            "cost":              cost,
            "price":             price,
            "stock":             qty,
            "stock_value":       stock_value,
            "revenue":           potential_revenue,
            "low_level":         low_level,
            "status":            status,
            "status_color":      status_color,
            "earliest_expiration": exp,
            "exp_days":          exp_days,
        })

        total_units += qty
        total_value += stock_value
        total_revenue += potential_revenue

    # ---- Expiring Soon (batches, non-expired) ----
    expiring = _get_expiring_batches(days=90)

    # ---- Group by category ----
    groups_map = {}
    for e in enriched:
        groups_map.setdefault(e["category"], []).append(e)

    groups = []
    for cat in sorted(groups_map.keys()):
        rows = sorted(groups_map[cat], key=lambda r: r["name"])
        subtotal = {
            "qty":     sum(r["stock"] for r in rows),
            "value":   sum(r["stock_value"] for r in rows),
            "revenue": sum(r["revenue"] for r in rows),
        }
        groups.append({
            "category": cat,
            "rows":     rows,
            "subtotal": subtotal,
        })

    summary = {
        "total_skus":     total_skus,
        "total_units":    total_units,
        "total_value":    total_value,
        "total_revenue":  total_revenue,
        "total_profit":   total_revenue - total_value,
        "low_count":      low_count,
        "out_count":      out_count,
        "expiring_count": len(expiring),
    }

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filters":      filters or {},
        "summary":      summary,
        "groups":       groups,
        "expiring":     expiring,
    }


# ─────────────────────────────────────────────
# DB HELPERS (used only by this report)
# ─────────────────────────────────────────────

def _stock_value_from_batches(product_id):
    """SUM(cost_price × quantity) across non-expired, non-archived batches."""
    conn = get_connection()
    today = now_local()[:10]
    row = conn.execute("""
        SELECT COALESCE(SUM(cost_price * quantity), 0) AS v
        FROM batches
        WHERE product_id = ?
          AND is_archived = 0
          AND (expiration_date IS NULL OR expiration_date >= ?)
    """, (product_id, today)).fetchone()
    conn.close()
    return row["v"] if row else 0


def _get_expiring_batches(days=90):
    conn = get_connection()
    today = now_local()[:10]
    rows = conn.execute("""
        SELECT b.batch_no, b.quantity, b.expiration_date,
               p.name AS product_name, p.brand, p.size, p.unit
        FROM batches b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.is_archived = 0
          AND b.quantity > 0
          AND b.expiration_date IS NOT NULL
          AND b.expiration_date >= ?
          AND b.expiration_date <= DATE(?, '+' || ? || ' days')
        ORDER BY b.expiration_date ASC
    """, (today, today, days)).fetchall()
    conn.close()

    today_date = datetime.now().date()
    result = []
    for r in rows:
        try:
            exp = datetime.strptime(r["expiration_date"], "%Y-%m-%d").date()
            days_left = (exp - today_date).days
        except ValueError:
            days_left = None

        name = " ".join(
            part for part in (r["brand"], r["product_name"], r["size"])
            if part
        )

        result.append({
            "batch_no":        r["batch_no"],
            "product_name":    name,
            "quantity":        r["quantity"],
            "expiration_date": r["expiration_date"],
            "days_left":       days_left,
        })

    return result


def _display_name(p):
    parts = [p.get("brand"), p.get("name"), p.get("size")]
    return " ".join(part for part in parts if part)


# ─────────────────────────────────────────────
# TEXT RENDERING (for the preview dialog)
# ─────────────────────────────────────────────

def render_inventory_report_text(data):
    """
    Return a plain-text rendering of the inventory report.
    Uses fixed-width columns for the preview.
    """
    W = 100  # total width

    lines = []

    def hr(char="="):
        return char * W

    def line(text=""):
        lines.append(text)

    # ---- Header ----
    line(hr("="))
    line("3F MiniMart".center(W))
    line("Inventory Report".center(W))
    line(f"Snapshot: {data['generated_at']}".center(W))
    if data.get("filters"):
        line(_filter_summary_line(data["filters"]).center(W))
    line(hr("="))

    # ---- Summary ----
    s = data["summary"]
    line("SUMMARY")
    line("-" * W)
    line(f"  Total SKUs           : {s['total_skus']:>6}")
    line(f"  Total Stock Units    : {s['total_units']:>6}")
    line(f"  Total Stock Value    : ₱{s['total_value']:>10,.2f}")
    line(f"  Potential Revenue    : ₱{s['total_revenue']:>10,.2f}")
    line(f"  Potential Profit     : ₱{s['total_profit']:>10,.2f}")
    line()
    line(f"  Low Stock: {s['low_count']}     "
         f"Out of Stock: {s['out_count']}     "
         f"Expiring Soon: {s['expiring_count']}")
    line(hr("="))

    # ---- Product table (grouped) ----
    line("PRODUCTS")
    line()

    # Column layout (fixed widths, total should stay under W)
    col_w = {
        "name":    34,
        "unit":     5,
        "cost":    10,
        "price":   10,
        "stock":    7,
        "value":   12,
        "status":   6,
    }

    header = (
        "Name".ljust(col_w["name"]) + " " +
        "Unit".center(col_w["unit"]) + " " +
        "Cost".rjust(col_w["cost"]) + " " +
        "Price".rjust(col_w["price"]) + " " +
        "Stock".rjust(col_w["stock"]) + " " +
        "Value".rjust(col_w["value"]) + " " +
        "Status".center(col_w["status"])
    )
    line(header)
    line("-" * len(header))

    for group in data["groups"]:
        # ---- Category heading ----
        cat_line = f"[{group['category'].upper()}]  ({len(group['rows'])} products)"
        line(cat_line)

        for r in group["rows"]:
            name = r["name"][:col_w["name"]].ljust(col_w["name"])
            row = (
                name + " " +
                (r["unit"][:col_w["unit"]]).center(col_w["unit"]) + " " +
                f"₱{r['cost']:,.2f}".rjust(col_w["cost"]) + " " +
                f"₱{r['price']:,.2f}".rjust(col_w["price"]) + " " +
                f"{r['stock']:>4}".rjust(col_w["stock"]) + " " +
                f"₱{r['stock_value']:,.2f}".rjust(col_w["value"]) + " " +
                r["status"].center(col_w["status"])
            )
            line("  " + row)

        sub = group["subtotal"]
        line(
            f"  Subtotal: {sub['qty']} units  •  "
            f"Stock Value ₱{sub['value']:,.2f}  •  "
            f"Revenue ₱{sub['revenue']:,.2f}"
        )
        line()

    # ---- Expiring Soon ----
    if data["expiring"]:
        line(hr("="))
        line(f"EXPIRING SOON  (next 90 days)")
        line("-" * W)
        line(
            "Batch No".ljust(22) + " " +
            "Product".ljust(38) + " " +
            "Qty".rjust(6) + " " +
            "Expires".rjust(12) + " " +
            "Days".rjust(6)
        )
        line("-" * W)

        for e in data["expiring"]:
            name = e["product_name"][:38].ljust(38)
            days = f"{e['days_left']}" if e["days_left"] is not None else "-"
            line(
                e["batch_no"].ljust(22) + " " +
                name + " " +
                f"{e['quantity']:>4}".rjust(6) + " " +
                e["expiration_date"].rjust(12) + " " +
                days.rjust(6)
            )

    line(hr("="))
    line("Stock Value = sum of (batch cost × batch quantity).".center(W))
    line("Status reflects stock vs. low-stock threshold.".center(W))
    line(hr("="))

    return "\n".join(lines)


def _filter_summary_line(filters):
    parts = []
    if filters.get("category"):
        parts.append(f"Category: {filters['category']}")
    if filters.get("search"):
        parts.append(f"Search: \"{filters['search']}\"")
    if filters.get("show_archived"):
        parts.append("Including archived")
    if filters.get("low_only"):
        parts.append("Low stock only")
    return "  •  ".join(parts) if parts else "All products"


# ─────────────────────────────────────────────
# PDF EXPORT
# ─────────────────────────────────────────────

def export_inventory_pdf(data, parent_window=None):
    """
    Save the inventory report data as a PDF.
    Returns (success, path_or_error).
    """
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
        title="3F MiniMart — Inventory Report",
        author="3F MiniMart POS",
    )

    styles = _make_styles()
    story = []

    # ---- Header ----
    story.append(Paragraph("3F MiniMart", styles["3f_brand"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Inventory Report", styles["3f_title"]))
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
        ["Total SKUs", f"{s['total_skus']:,}",
         "Total Stock Units", f"{s['total_units']:,}"],
        ["Stock Value", f"₱{s['total_value']:,.2f}",
         "Potential Revenue", f"₱{s['total_revenue']:,.2f}"],
        ["Potential Profit", f"₱{s['total_profit']:,.2f}",
         "Expiring Soon", f"{s['expiring_count']:,}"],
        ["Low Stock", f"{s['low_count']:,}",
         "Out of Stock", f"{s['out_count']:,}"],
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

    # ---- Products table, grouped by category ----
    story.append(Paragraph("Products by Category", styles["3f_section"]))
    story.append(Spacer(1, 6))

    col_widths = [
        2.40 * inch,   # Name
        0.45 * inch,   # Unit
        0.65 * inch,   # Cost
        0.65 * inch,   # Price
        0.55 * inch,   # Stock
        0.85 * inch,   # Value
        0.55 * inch,   # Status
    ]

    header = ["Name", "Unit", "Cost", "Price", "Stock", "Value", "Status"]
    rows = [header]
    styles_cmds = [
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

    r = 1  # current row index
    for group in data["groups"]:
        # ---- Category header row (spans all columns) ----
        rows.append([f"[{group['category'].upper()}]  "
                     f"({len(group['rows'])} products)",
                     "", "", "", "", "", ""])
        styles_cmds.append(
            ("SPAN", (0, r), (-1, r))
        )
        styles_cmds.append(
            ("BACKGROUND", (0, r), (-1, r), CAT_BG)
        )
        styles_cmds.append(
            ("FONT", (0, r), (-1, r), FONT_BOLD, 9)
        )
        styles_cmds.append(
            ("TEXTCOLOR", (0, r), (-1, r), BRAND_BLUE)
        )
        r += 1

        for item in group["rows"]:
            rows.append([
                item["name"],
                item["unit"],
                f"₱{item['cost']:,.2f}",
                f"₱{item['price']:,.2f}",
                f"{item['stock']:,}",
                f"₱{item['stock_value']:,.2f}",
                item["status"],
            ])
            # ---- Status color ----
            sc = item["status_color"]
            color = {
                "danger": DANGER,
                "amber":  AMBER,
                "ok":     SUCCESS,
            }.get(sc, FG_PRIMARY)
            styles_cmds.append(("TEXTCOLOR", (6, r), (6, r), color))
            styles_cmds.append(("FONT", (6, r), (6, r), FONT_BOLD, 9))
            r += 1

        # ---- Subtotal row ----
        sub = group["subtotal"]
        rows.append([
            "Subtotal",
            "",
            "",
            "",
            f"{sub['qty']:,}",
            f"₱{sub['value']:,.2f}",
            "",
        ])
        styles_cmds.append(("SPAN", (0, r), (3, r)))
        styles_cmds.append(("BACKGROUND", (0, r), (-1, r), SUB_BG))
        styles_cmds.append(("FONT", (0, r), (-1, r), FONT_BOLD, 9))
        styles_cmds.append(("ALIGN", (0, r), (0, r), "RIGHT"))
        r += 1

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(styles_cmds))
    story.append(table)

    # ---- Expiring Soon section ----
    if data["expiring"]:
        story.append(Spacer(1, 24))
        story.append(Paragraph("Expiring Soon (next 90 days)",
                               styles["3f_section"]))
        story.append(Spacer(1, 6))

        exp_rows = [["Batch No", "Product", "Qty", "Expires", "Days"]]
        exp_style = [
            ("BACKGROUND",   (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONT",         (0, 0), (-1, 0), FONT_BOLD, 9),
            ("ALIGN",        (2, 0), (4, -1), "RIGHT"),
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
        for i, e in enumerate(data["expiring"], start=1):
            days = f"{e['days_left']}" if e["days_left"] is not None else "-"
            exp_rows.append([
                e["batch_no"],
                e["product_name"],
                f"{e['quantity']:,}",
                e["expiration_date"],
                days,
            ])
            # Color days red if <=7, amber if <=30
            if e["days_left"] is not None:
                if e["days_left"] <= 7:
                    exp_style.append(("TEXTCOLOR", (4, i), (4, i), DANGER))
                elif e["days_left"] <= 30:
                    exp_style.append(("TEXTCOLOR", (4, i), (4, i), AMBER))

        exp_table = Table(
            exp_rows,
            colWidths=[1.4 * inch, 3.0 * inch,
                       0.7 * inch, 1.0 * inch, 0.7 * inch],
            repeatRows=1,
        )
        exp_table.setStyle(TableStyle(exp_style))
        story.append(exp_table)

    # ---- Footer ----
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Stock Value = sum of (batch cost × batch quantity) across "
        "non-expired batches. Status reflects stock level vs. low-stock threshold.",
        styles["3f_footnote"],
    ))

    doc.build(story)


# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────

def _make_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="3f_brand",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=22,
        leading=26,
        textColor=BRAND_GREEN,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="3f_title",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=15,
        leading=18,
        textColor=FG_PRIMARY,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="3f_subtitle",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=12,
        textColor=FG_MUTED,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="3f_section",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        textColor=FG_PRIMARY,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="3f_footnote",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=8,
        leading=11,
        textColor=FG_MUTED,
        alignment=TA_LEFT,
    ))

    return styles