# ─────────────────────────────────────────────
# PDF EXPORT (single purchase order)
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
# FONT REGISTRATION (needed for the ₱ symbol)
# ─────────────────────────────────────────────

FONT_REGULAR = "Helvetica"
FONT_BOLD    = "Helvetica-Bold"
FONT_ITALIC  = "Helvetica-Oblique"

def _register_fonts():
    global FONT_REGULAR, FONT_BOLD, FONT_ITALIC
    try:
        import reportlab
        rl_dir = os.path.dirname(reportlab.__file__)
        fonts_dir = os.path.join(rl_dir, "fonts")

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
STATUS_ORDERED   = colors.HexColor("#D97706")
STATUS_RECEIVED  = colors.HexColor("#16A34A")
STATUS_CANCELLED = colors.HexColor("#DC2626")


# ─────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────

def export_purchase_pdf(purchase, items, parent_window=None):
    """
    Export a single purchase order to PDF.

    Parameters
    ----------
    purchase : dict
        Purchase record (purchase_id, supplier_name, status, total_cost,
        full_name, username, created_at, received_at, notes).
    items : list[dict]
        Line items (product_code, product_name, quantity, cost).
    parent_window : tk widget or None
        Parent for the file dialog.

    Returns
    -------
    (ok, result) : tuple[bool, str]
        ok=True and result=path on success.
        ok=False and result="Cancelled." if user closed the dialog.
        ok=False and result=<error message> on failure.
    """
    default_name = _default_filename(purchase)
    path = filedialog.asksaveasfilename(
        title=f"Save PO #{purchase.get('purchase_id', '')}",
        defaultextension=".pdf",
        initialfile=default_name,
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        parent=parent_window,
    )
    if not path:
        return False, "Cancelled."

    try:
        _build_pdf(path, purchase, items)
        return True, path
    except Exception as e:
        return False, str(e)


def _default_filename(purchase):
    today = datetime.now().strftime("%Y%m%d")
    pid = purchase.get("purchase_id", "unknown")
    return f"3F_PO_{pid}_{today}.pdf"


# ─────────────────────────────────────────────
# PDF BUILDER
# ─────────────────────────────────────────────

def _build_pdf(path, purchase, items):
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"3F MiniMart — PO #{purchase.get('purchase_id', '')}",
        author="3F MiniMart POS",
    )

    styles = _make_styles()
    story = []

    # ═════════════════════════════════════════
    # HEADER
    # ═════════════════════════════════════════

    story.append(Paragraph("3F MiniMart", styles["3f_brand"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Purchase Order #{purchase.get('purchase_id', '-')}",
        styles["3f_title"],
    ))
    story.append(Spacer(1, 4))

    subtitle_parts = [
        f"Supplier: {purchase.get('supplier_name') or 'Unknown'}",
        f"Status: {purchase.get('status') or '-'}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]
    story.append(Paragraph("  •  ".join(subtitle_parts), styles["3f_subtitle"]))
    story.append(Spacer(1, 20))

    # ═════════════════════════════════════════
    # DETAILS
    # ═════════════════════════════════════════

    story.append(Paragraph("Details", styles["3f_section"]))
    story.append(Spacer(1, 8))

    status = purchase.get("status") or "-"
    if status == "Received":
        status_color = STATUS_RECEIVED
    elif status == "Cancelled":
        status_color = STATUS_CANCELLED
    else:
        status_color = STATUS_ORDERED

    details_data = [
        ["Status",         status],
        ["Ordered By",     purchase.get("full_name")
                            or purchase.get("username") or "-"],
        ["Date Ordered",   purchase.get("created_at") or "-"],
        ["Date Received",  purchase.get("received_at") or "-"],
        ["Notes",          purchase.get("notes") or "-"],
    ]

    details_table = Table(
        details_data,
        colWidths=[1.6 * inch, 5.5 * inch],
    )
    details_table.setStyle(TableStyle([
        ("FONT",          (0, 0), (0, -1), FONT_BOLD, 10),
        ("FONT",          (1, 0), (1, -1), FONT_REGULAR, 10),
        ("TEXTCOLOR",     (0, 0), (0, -1), FG_MUTED),
        ("TEXTCOLOR",     (1, 0), (1, -1), FG_PRIMARY),
        ("BACKGROUND",    (0, 0), (-1, -1), ROW_ALT),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, BORDER_GREY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 22))

    # ═════════════════════════════════════════
    # ITEMS
    # ═════════════════════════════════════════

    story.append(Paragraph("Items", styles["3f_section"]))
    story.append(Spacer(1, 8))

    if not items:
        story.append(Paragraph(
            "No items on this purchase order.",
            styles["3f_empty"],
        ))
    else:
        rows = [["#", "Code", "Product", "Qty", "Unit Cost", "Subtotal"]]
        for i, it in enumerate(items, start=1):
            name = it.get("product_name") or "-"
            qty  = it.get("quantity", 0) or 0
            cost = it.get("cost", 0) or 0
            subtotal = qty * cost
            rows.append([
                str(i),
                it.get("product_code") or "-",
                _truncate(name, 45),
                f"{qty}",
                f"₱{cost:,.2f}",
                f"₱{subtotal:,.2f}",
            ])

        # ---- Total row ----
        total = purchase.get("total_cost") or sum(
            (it.get("quantity", 0) or 0) * (it.get("cost", 0) or 0)
            for it in items
        )
        rows.append(["", "", "", "", "TOTAL", f"₱{total:,.2f}"])

        col_widths = [
            0.35 * inch,  # #
            0.90 * inch,  # Code
            3.00 * inch,  # Product
            0.60 * inch,  # Qty
            1.00 * inch,  # Unit Cost
            1.25 * inch,  # Subtotal
        ]

        table = Table(rows, colWidths=col_widths, repeatRows=1)

        style_cmds = [
            ("BACKGROUND",   (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONT",         (0, 0), (-1, 0), FONT_BOLD, 9),
            ("FONT",         (0, 1), (-1, -2), FONT_REGULAR, 9),
            ("FONT",         (4, -1), (-1, -1), FONT_BOLD, 10),
            ("TEXTCOLOR",    (0, 1), (-1, -1), FG_PRIMARY),
            ("ALIGN",        (3, 0), (-1, -1), "RIGHT"),
            ("LINEBELOW",    (0, 0), (-1, 0), 0.5, BRAND_BLUE),
            ("LINEBELOW",    (0, 1), (-1, -2), 0.25, BORDER_GREY),
            ("LINEABOVE",    (0, -1), (-1, -1), 0.5, BRAND_BLUE),
            ("BACKGROUND",   (0, -1), (-1, -1), ROW_ALT),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ]
        for i in range(1, len(rows) - 1):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))

        table.setStyle(TableStyle(style_cmds))
        story.append(table)

    # ═════════════════════════════════════════
    # FOOTER
    # ═════════════════════════════════════════

    story.append(Spacer(1, 24))
    story.append(Paragraph(
        "This document is a record of the purchase order as recorded "
        "in the 3F MiniMart system.",
        styles["3f_footnote"],
    ))

    doc.build(story)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

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
        name="3f_brand",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=22,
        leading=26,
        textColor=BRAND_GREEN,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="3f_title",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=15,
        leading=18,
        textColor=FG_PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="3f_subtitle",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=12,
        textColor=FG_MUTED,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="3f_section",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        textColor=FG_PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="3f_empty",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=10,
        leading=13,
        textColor=FG_MUTED,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="3f_footnote",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=8,
        leading=11,
        textColor=FG_MUTED,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))

    return styles