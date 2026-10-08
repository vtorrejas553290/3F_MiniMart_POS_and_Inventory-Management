# ─────────────────────────────────────────────
# PDF EXPORT (sales report)
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
PROFIT_POS  = colors.HexColor("#16A34A")
PROFIT_NEG  = colors.HexColor("#DC2626")


# ─────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────

def export_sales_report(summary, top_products,
                        date_from=None, date_to=None,
                        payment_filter="All",
                        exporter_name="",
                        parent_window=None):
    default_name = _default_filename(date_from, date_to)
    path = filedialog.asksaveasfilename(
        title="Save Sales Report",
        defaultextension=".pdf",
        initialfile=default_name,
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        parent=parent_window,
    )
    if not path:
        return False, "Cancelled."

    try:
        _build_pdf(path, summary, top_products,
                   date_from, date_to, payment_filter,
                   exporter_name)
        return True, path
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────
# FILENAME
# ─────────────────────────────────────────────

def _default_filename(date_from, date_to):
    today = datetime.now().strftime("%Y%m%d")
    if date_from and date_to and date_from == date_to:
        return f"3F_Sales_{date_from}_{today}.pdf"
    if date_from and date_to:
        return f"3F_Sales_{date_from}_to_{date_to}.pdf"
    return f"3F_Sales_AllTime_{today}.pdf"


# ─────────────────────────────────────────────
# PDF BUILDER
# ─────────────────────────────────────────────

def _build_pdf(path, summary, top_products,
               date_from, date_to, payment_filter,
               exporter_name=""):
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title="3F MiniMart — Sales Report",
        author="3F MiniMart POS",
    )

    styles = _make_styles()
    story = []

    # ═════════════════════════════════════════
    # HEADER
    # ═════════════════════════════════════════

    story.append(Paragraph("3F MiniMart", styles["3f_brand"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Sales Report", styles["3f_title"]))
    story.append(Spacer(1, 4))

    subtitle_parts = [_date_range_label(date_from, date_to)]
    if payment_filter and payment_filter != "All":
        subtitle_parts.append(f"Payment: {payment_filter}")
    subtitle_parts.append(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    story.append(Paragraph("  •  ".join(subtitle_parts), styles["3f_subtitle"]))
    story.append(Spacer(1, 22))

    # ═════════════════════════════════════════
    # SUMMARY
    # ═════════════════════════════════════════

    story.append(Paragraph("Summary", styles["3f_section"]))
    story.append(Spacer(1, 8))

    total_sales = summary.get("total_sales", 0) or 0
    count       = summary.get("count", 0) or 0
    cash_total  = summary.get("cash_total", 0) or 0
    gcash_total = summary.get("gcash_total", 0) or 0

    summary_data = [
        ["Total Sales", f"₱{total_sales:,.2f}", "Transactions", f"{count:,}"],
        ["Cash",        f"₱{cash_total:,.2f}",  "GCash",        f"₱{gcash_total:,.2f}"],
    ]
    summary_table = Table(summary_data,
                          colWidths=[1.3 * inch, 1.6 * inch,
                                     1.3 * inch, 1.6 * inch])
    summary_table.setStyle(TableStyle([
        ("FONT",         (0, 0), (0, -1), FONT_BOLD, 10),
        ("FONT",         (2, 0), (2, -1), FONT_BOLD, 10),
        ("FONT",         (1, 0), (1, -1), FONT_BOLD, 15),
        ("FONT",         (3, 0), (3, -1), FONT_BOLD, 15),
        ("TEXTCOLOR",    (0, 0), (0, -1), FG_MUTED),
        ("TEXTCOLOR",    (2, 0), (2, -1), FG_MUTED),
        ("TEXTCOLOR",    (1, 0), (1, -1), BRAND_BLUE),
        ("TEXTCOLOR",    (3, 0), (3, -1), FG_PRIMARY),
        ("BACKGROUND",   (0, 0), (-1, -1), ROW_ALT),
        ("BOX",          (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("INNERGRID",    (0, 0), (-1, -1), 0.25, BORDER_GREY),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 26))

    # ═════════════════════════════════════════
    # TOP SELLING PRODUCTS
    # ═════════════════════════════════════════

    story.append(Paragraph("Top Selling Products", styles["3f_section"]))
    story.append(Spacer(1, 8))

    if not top_products:
        story.append(Paragraph(
            "No sales data available for the selected period.",
            styles["3f_empty"],
        ))
    else:
        header = ["#", "Product", "Code", "Units",
                  "Cost", "Price", "Profit", "Revenue"]
        rows = [header]

        for i, p in enumerate(top_products, start=1):
            display = " ".join(
                part for part in (p.get("brand"),
                                  p.get("product_name"),
                                  p.get("size"))
                if part
            )
            rows.append([
                str(i),
                _truncate(display, 40),
                p.get("product_code") or "-",
                f"{p.get('units_sold', 0):,}",
                f"₱{p.get('avg_cost', 0):.2f}",
                f"₱{p.get('avg_price', 0):.2f}",
                f"₱{p.get('profit', 0):.2f}",
                f"₱{p.get('revenue', 0):,.2f}",
            ])

        col_widths = [
            0.30 * inch,  # #
            2.30 * inch,  # Product
            0.80 * inch,  # Code
            0.55 * inch,  # Units
            0.70 * inch,  # Cost
            0.70 * inch,  # Price
            0.80 * inch,  # Profit
            0.95 * inch,  # Revenue
        ]

        table = Table(rows, colWidths=col_widths, repeatRows=1)
        style_cmds = [
            ("BACKGROUND",   (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONT",         (0, 0), (-1, 0), FONT_BOLD, 9),
            ("ALIGN",        (0, 0), (0, -1), "LEFT"),
            ("ALIGN",        (3, 0), (-1, -1), "RIGHT"),
            ("FONT",         (0, 1), (-1, -1), FONT_REGULAR, 9),
            ("FONT",         (1, 1), (1, -1), FONT_BOLD, 9),
            ("FONT",         (7, 1), (7, -1), FONT_BOLD, 9),
            ("TEXTCOLOR",    (0, 1), (-1, -1), FG_PRIMARY),
            ("TEXTCOLOR",    (7, 1), (7, -1), BRAND_BLUE),
            ("LINEBELOW",    (0, 0), (-1, 0), 0.5, BRAND_BLUE),
            ("LINEBELOW",    (0, 1), (-1, -1), 0.25, BORDER_GREY),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ]
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))

        for i, p in enumerate(top_products, start=1):
            profit = p.get("profit", 0)
            color = PROFIT_POS if profit > 0 else (
                PROFIT_NEG if profit < 0 else FG_MUTED
            )
            style_cmds.append(("TEXTCOLOR", (6, i), (6, i), color))

        table.setStyle(TableStyle(style_cmds))
        story.append(table)

    # ═════════════════════════════════════════
    # FOOTER
    # ═════════════════════════════════════════

    story.append(Spacer(1, 28))
    story.append(Paragraph(
        f"Exported by: {exporter_name or '-'}",
        styles["3f_footnote"],
    ))
    story.append(Paragraph(
        f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["3f_footnote"],
    ))

    doc.build(story)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _date_range_label(date_from, date_to):
    if not date_from and not date_to:
        return "All time"
    if date_from and date_to:
        if date_from == date_to:
            return f"Date: {date_from}"
        return f"Date: {date_from} to {date_to}"
    return f"Date: {date_from or '…'} to {date_to or '…'}"


def _truncate(text, max_len):
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"


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
        name="3f_empty", parent=styles["Normal"],
        fontName=FONT_ITALIC, fontSize=10, leading=13,
        textColor=FG_MUTED, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="3f_footnote", parent=styles["Normal"],
        fontName=FONT_ITALIC, fontSize=8, leading=11,
        textColor=FG_MUTED, alignment=TA_LEFT,
    ))

    return styles