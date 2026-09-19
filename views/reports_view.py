# ─────────────────────────────────────────────
# REPORTS VIEW (softened 3F MiniMart branding + summary)
# ─────────────────────────────────────────────

import customtkinter as ctk
from datetime import datetime, timedelta

from controllers.report_controller import ReportController
from utils import prepare_dialog_screen
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BG_INPUT, BG_ROW_ALT, BORDER,
    FG_PRIMARY, FG_SECONDARY, FG_MUTED,
    BRAND_GREEN, BRAND_YELLOW,
    ACCENT, ACCENT_HOVER, SUCCESS, DANGER, DANGER_HOVER,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


# ─────────────────────────────────────────────
# REPORTS VIEW
# ─────────────────────────────────────────────

class ReportsView(ctk.CTkFrame):

    # ─────────────────────────────────────────────
    # BUTTON COLORS
    # ─────────────────────────────────────────────

    ACTIVE_COLOR = ACCENT
    IDLE_COLOR   = NEUTRAL

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user

        # ---- Filter state ----
        self.date_from = ""
        self.date_to = ""
        self.search_query = ""
        self.payment_filter = "All"

        # ---- Active quick-range button ----
        self.active_range_button = None
        self._programmatic_set = False

        self._build()
        self._refresh_transactions()

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        # ═════════════════════════════════════════
        # PAGE HEADER
        # ═════════════════════════════════════════

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box, text="Reports",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="View individual sales transactions",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ═════════════════════════════════════════
        # SUMMARY CARD (fixed 110px height)
        # ═════════════════════════════════════════

        summary_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                    corner_radius=12,
                                    border_width=1,
                                    border_color=BORDER,
                                    height=110)
        summary_card.pack(fill="x", padx=20, pady=(0, 10))
        summary_card.pack_propagate(False)

        # ---- Left: Total Sales ----
        left_stat = ctk.CTkFrame(summary_card, fg_color="transparent")
        left_stat.pack(side="left", fill="both", padx=20, pady=14)

        ctk.CTkLabel(left_stat, text="TOTAL SALES",
                     font=font_bold(10),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x")
        self.total_sales_label = ctk.CTkLabel(left_stat, text="₱0.00",
                                              font=font_bold(24),
                                              text_color=ACCENT,
                                              anchor="w")
        self.total_sales_label.pack(fill="x", pady=(2, 0))

        # ---- Divider ----
        ctk.CTkFrame(summary_card, width=1, fg_color=BORDER).pack(
            side="left", fill="y", pady=14)

        # ---- Middle: Transactions ----
        mid_stat = ctk.CTkFrame(summary_card, fg_color="transparent")
        mid_stat.pack(side="left", fill="both", padx=20, pady=14)

        ctk.CTkLabel(mid_stat, text="TRANSACTIONS",
                     font=font_bold(10),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x")
        self.txn_count_label = ctk.CTkLabel(mid_stat, text="0",
                                            font=font_bold(24),
                                            text_color=FG_PRIMARY,
                                            anchor="w")
        self.txn_count_label.pack(fill="x", pady=(2, 0))

        # ---- Divider ----
        ctk.CTkFrame(summary_card, width=1, fg_color=BORDER).pack(
            side="left", fill="y", pady=14)

        # ---- Right: Payment breakdown (fixed width) ----
        right_stat = ctk.CTkFrame(summary_card, fg_color="transparent",
                                  width=260)     # ---- fixed width ----
        right_stat.pack(side="left", fill="y", padx=20, pady=14)
        right_stat.pack_propagate(False)         # ---- keep 260px ----

        ctk.CTkLabel(right_stat, text="PAYMENT BREAKDOWN",
                     font=font_bold(10),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x")

        # ---- Cash row (label + amount on same line, close together) ----
        cash_row = ctk.CTkFrame(right_stat, fg_color="transparent")
        cash_row.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(cash_row, text="Cash",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left")
        self.cash_total_label = ctk.CTkLabel(cash_row, text="₱0.00",
                                             font=font_bold(12),
                                             text_color=SUCCESS)
        self.cash_total_label.pack(side="right")

        # ---- GCash row ----
        gcash_row = ctk.CTkFrame(right_stat, fg_color="transparent")
        gcash_row.pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(gcash_row, text="GCash",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left")
        self.gcash_total_label = ctk.CTkLabel(gcash_row, text="₱0.00",
                                              font=font_bold(12),
                                              text_color=ACCENT)
        self.gcash_total_label.pack(side="right")

        # ---- Date range label (far right of the card) ----
        self.range_label = ctk.CTkLabel(summary_card, text="",
                                        font=font(10),
                                        text_color=FG_MUTED)
        self.range_label.place(relx=0.985, rely=0.5, anchor="e")

        # ═════════════════════════════════════════
        # FILTER CARD
        # ═════════════════════════════════════════

        filter_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                   corner_radius=12,
                                   border_width=1,
                                   border_color=BORDER)
        filter_card.pack(fill="x", padx=20, pady=(0, 10))

        # ---- Row 1: search + payment + refresh ----
        row1 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(row1, text="Search",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        self.search_e = ctk.CTkEntry(
            row1,
            placeholder_text="Search by txn #, cashier, payment, product name...",
            textvariable=self.search_var,
            width=340, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
        )
        self.search_e.pack(side="left", padx=(0, 8))

        ctk.CTkButton(row1, text="✕", width=36, height=36,
                      corner_radius=8,
                      font=font(13),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._clear_search).pack(side="left", padx=(0, 20))

        # ---- Payment filter ----
        ctk.CTkLabel(row1, text="Payment",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.payment_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            row1,
            values=["All", "Cash", "GCash"],
            variable=self.payment_var,
            width=140, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=NEUTRAL,
            text_color=FG_PRIMARY,
            command=self._on_payment_change,
        ).pack(side="left", padx=(0, 20))

        # ---- Refresh button ----
        ctk.CTkButton(row1, text="Refresh", width=100, height=36,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._refresh_transactions).pack(side="right")

        # ---- Row 2: date range ----
        row2 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(row2, text="Date From",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.date_from_var = ctk.StringVar()
        self.date_from_var.trace_add("write", self._on_date_change)

        self.date_from_e = ctk.CTkEntry(
            row2, placeholder_text="YYYY-MM-DD",
            textvariable=self.date_from_var,
            width=130, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
        )
        self.date_from_e.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row2, text="Date To",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.date_to_var = ctk.StringVar()
        self.date_to_var.trace_add("write", self._on_date_change)

        self.date_to_e = ctk.CTkEntry(
            row2, placeholder_text="YYYY-MM-DD",
            textvariable=self.date_to_var,
            width=130, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
        )
        self.date_to_e.pack(side="left", padx=(0, 16))

        # ---- Quick range buttons ----
        self.btn_today = ctk.CTkButton(
            row2, text="Today", width=80, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._range_today,
        )
        self.btn_today.pack(side="left", padx=2)

        self.btn_7days = ctk.CTkButton(
            row2, text="Last 7 Days", width=100, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._range_7_days,
        )
        self.btn_7days.pack(side="left", padx=2)

        self.btn_month = ctk.CTkButton(
            row2, text="This Month", width=100, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._range_this_month,
        )
        self.btn_month.pack(side="left", padx=2)

        self.btn_clear = ctk.CTkButton(
            row2, text="Clear Dates", width=100, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._clear_dates,
        )
        self.btn_clear.pack(side="left", padx=2)

        # ---- Results count ----
        self.count_label = ctk.CTkLabel(row2, text="",
                                        font=font_bold(11),
                                        text_color=FG_SECONDARY)
        self.count_label.pack(side="right", padx=(0, 4))

        # ═════════════════════════════════════════
        # LIST CARD (fills all remaining space)
        # ═════════════════════════════════════════

        list_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                 corner_radius=12,
                                 border_width=1,
                                 border_color=BORDER)
        list_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    # ─────────────────────────────────────────────
    # FILTERS — SEARCH
    # ─────────────────────────────────────────────

    def _on_search_change(self, *args):
        self.search_query = self.search_var.get().strip().lower()
        self._refresh_transactions()

    def _clear_search(self):
        self.search_var.set("")

    # ─────────────────────────────────────────────
    # FILTERS — PAYMENT METHOD
    # ─────────────────────────────────────────────

    def _on_payment_change(self, choice):
        self.payment_filter = choice
        self._refresh_transactions()

    # ─────────────────────────────────────────────
    # QUICK-RANGE BUTTON HIGHLIGHT
    # ─────────────────────────────────────────────

    def _highlight_button(self, button):
        if self.active_range_button is not None:
            self.active_range_button.configure(
                fg_color=NEUTRAL, text_color=NEUTRAL_TEXT,
            )
        if button is not None:
            button.configure(fg_color=ACCENT, text_color="#FFFFFF")
        self.active_range_button = button

    def _clear_button_highlight(self):
        if self.active_range_button is not None:
            self.active_range_button.configure(
                fg_color=NEUTRAL, text_color=NEUTRAL_TEXT,
            )
        self.active_range_button = None

    # ─────────────────────────────────────────────
    # FILTERS — DATE RANGE (auto-apply)
    # ─────────────────────────────────────────────

    def _on_date_change(self, *args):
        if self._programmatic_set:
            return

        d_from = self.date_from_var.get().strip()
        d_to = self.date_to_var.get().strip()

        if d_from and len(d_from) < 10:
            return
        if d_to and len(d_to) < 10:
            return
        if d_from and not self._is_valid_date(d_from):
            return
        if d_to and not self._is_valid_date(d_to):
            return
        if d_from and d_to and d_from > d_to:
            return

        self._clear_button_highlight()
        self.date_from = d_from
        self.date_to = d_to
        self._refresh_transactions()

    def _is_valid_date(self, text):
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    # ─────────────────────────────────────────────
    # QUICK RANGES
    # ─────────────────────────────────────────────

    def _range_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self._set_dates_programmatically(today, today, self.btn_today)

    def _range_7_days(self):
        today = datetime.now()
        start = (today - timedelta(days=6)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        self._set_dates_programmatically(start, end, self.btn_7days)

    def _range_this_month(self):
        today = datetime.now()
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        self._set_dates_programmatically(start, end, self.btn_month)

    def _clear_dates(self):
        self._set_dates_programmatically("", "", self.btn_clear)

    # ─────────────────────────────────────────────
    # HELPER — PROGRAMMATIC DATE SET
    # ─────────────────────────────────────────────

    def _set_dates_programmatically(self, d_from, d_to, button):
        self._programmatic_set = True
        self.date_from_var.set(d_from)
        self.date_to_var.set(d_to)
        self._programmatic_set = False

        self.date_from = d_from
        self.date_to = d_to
        self._highlight_button(button)
        self._refresh_transactions()

    # ─────────────────────────────────────────────
    # REFRESH
    # ─────────────────────────────────────────────

    def _refresh_transactions(self):
        rows = ReportController.list_transactions(
            date_from=self.date_from or None,
            date_to=self.date_to or None,
            search=self.search_query or None,
            payment_method=self.payment_filter,
        )

        self._update_summary(rows)
        self._render(rows)

    def _update_summary(self, transactions):
        total_sales = sum(t["total"] for t in transactions)
        count = len(transactions)

        cash_total = sum(t["total"] for t in transactions
                         if t["payment_method"] == "Cash")
        gcash_total = sum(t["total"] for t in transactions
                          if t["payment_method"] == "GCash")

        self.total_sales_label.configure(text=f"₱{total_sales:,.2f}")
        self.txn_count_label.configure(text=f"{count:,}")
        self.cash_total_label.configure(text=f"₱{cash_total:,.2f}")
        self.gcash_total_label.configure(text=f"₱{gcash_total:,.2f}")

        if self.date_from or self.date_to:
            d_from = self.date_from or "…"
            d_to = self.date_to or "…"
            self.range_label.configure(text=f"{d_from}  →  {d_to}")
        else:
            self.range_label.configure(text="All time")

    # ─────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────

    def _render(self, transactions):
        for w in self.list_frame.winfo_children():
            w.destroy()

        self.count_label.configure(text=f"{len(transactions)} transaction(s)")

        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))
        cols = [
            ("Txn #",       70),
            ("Date & Time", 140),
            ("Cashier",     110),
            ("Payment",     80),
            ("Item",        220),
            ("Qty",         50),
            ("Unit Price",  90),
            ("Subtotal",    90),
            ("Total",       90),
        ]
        for text, width in cols:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

        if not transactions:
            ctk.CTkLabel(self.list_frame,
                         text="No transactions match your filters.",
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            return

        for i, t in enumerate(transactions):
            self._render_row(t, i)

    def _render_row(self, t, txn_index=0):
        items = ReportController.transaction_items(t["transaction_id"])
        base_bg = BG_ROW_ALT if txn_index % 2 else BG_CARD

        if not items:
            row = ctk.CTkFrame(self.list_frame, fg_color=base_bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=f"#{t['transaction_id']}",
                         width=70, anchor="w",
                         font=font_bold(11),
                         text_color=ACCENT).pack(side="left", padx=3, pady=6)
            ctk.CTkLabel(row, text=t["created_at"] or "-",
                         width=140, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=t["full_name"] or t["username"] or "-",
                         width=110, anchor="w",
                         font=font(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=t["payment_method"],
                         width=80, anchor="w",
                         font=font_bold(11),
                         text_color=self._payment_color(t["payment_method"])
                         ).pack(side="left", padx=3)
            ctk.CTkLabel(row, text="—", width=220, anchor="w",
                         font=font(11),
                         text_color=FG_MUTED).pack(side="left", padx=3)
            ctk.CTkLabel(row, text="—", width=50,
                         text_color=FG_MUTED).pack(side="left", padx=3)
            ctk.CTkLabel(row, text="—", width=90,
                         text_color=FG_MUTED).pack(side="left", padx=3)
            ctk.CTkLabel(row, text="—", width=90,
                         text_color=FG_MUTED).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=f"₱{t['total']:.2f}",
                         width=90, anchor="w",
                         font=font_bold(12),
                         text_color=ACCENT).pack(side="left", padx=3)
            ctk.CTkButton(row, text="View", width=60, height=28,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=ACCENT, hover_color=ACCENT_HOVER,
                          command=lambda txn=t: self._view_transaction(txn)
                          ).pack(side="right", padx=4)
            return

        for index, it in enumerate(items):
            row = ctk.CTkFrame(self.list_frame, fg_color=base_bg, corner_radius=6)
            row.pack(fill="x", pady=1)

            if index == 0:
                ctk.CTkLabel(row, text=f"#{t['transaction_id']}",
                             width=70, anchor="w",
                             font=font_bold(11),
                             text_color=ACCENT).pack(side="left", padx=3, pady=6)
                ctk.CTkLabel(row, text=t["created_at"] or "-",
                             width=140, anchor="w",
                             font=font(11),
                             text_color=FG_SECONDARY).pack(side="left", padx=3)
                ctk.CTkLabel(row,
                             text=t["full_name"] or t["username"] or "-",
                             width=110, anchor="w",
                             font=font(11),
                             text_color=FG_PRIMARY).pack(side="left", padx=3)
                ctk.CTkLabel(row, text=t["payment_method"],
                             width=80, anchor="w",
                             font=font_bold(11),
                             text_color=self._payment_color(t["payment_method"])
                             ).pack(side="left", padx=3)
            else:
                ctk.CTkLabel(row, text="", width=70).pack(side="left", padx=3, pady=6)
                ctk.CTkLabel(row, text="", width=140).pack(side="left", padx=3)
                ctk.CTkLabel(row, text="", width=110).pack(side="left", padx=3)
                ctk.CTkLabel(row, text="", width=80).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=it["product_name"],
                         width=220, anchor="w",
                         font=font(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=f"×{it['quantity']}",
                         width=50, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=f"₱{it['price']:.2f}",
                         width=90, anchor="w",
                         font=font(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=f"₱{it['subtotal']:.2f}",
                         width=90, anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)

            if index == 0:
                ctk.CTkLabel(row, text=f"₱{t['total']:.2f}",
                             width=90, anchor="w",
                             font=font_bold(12),
                             text_color=ACCENT).pack(side="left", padx=3)
                ctk.CTkButton(row, text="View", width=60, height=28,
                              corner_radius=6,
                              font=font_bold(11),
                              fg_color=ACCENT, hover_color=ACCENT_HOVER,
                              command=lambda txn=t: self._view_transaction(txn)
                              ).pack(side="right", padx=4)
            else:
                ctk.CTkLabel(row, text="", width=90).pack(side="left", padx=3)
                ctk.CTkLabel(row, text="", width=64).pack(side="right", padx=4)

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────

    @staticmethod
    def _payment_color(method):
        if method == "Cash":
            return SUCCESS
        if method == "GCash":
            return ACCENT
        return FG_SECONDARY

    # ─────────────────────────────────────────────
    # TRANSACTION DETAIL
    # ─────────────────────────────────────────────

    def _view_transaction(self, txn):
        TransactionDetailDialog(self.winfo_toplevel(), txn)


# ─────────────────────────────────────────────
# TRANSACTION DETAIL DIALOG (styled)
# ─────────────────────────────────────────────

class TransactionDetailDialog(ctk.CTkToplevel):

    def __init__(self, parent, txn):
        super().__init__(parent)
        self.parent = parent
        self.txn = txn
        self.title(f"Transaction #{txn['transaction_id']}")
        self.geometry("580x500")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        t = self.txn

        ctk.CTkLabel(self, text=f"Transaction #{t['transaction_id']}",
                     font=font_bold(18),
                     text_color=FG_PRIMARY).pack(pady=(18, 4))

        ctk.CTkLabel(self, text=t["created_at"],
                     font=font(11),
                     text_color=FG_SECONDARY).pack(pady=(0, 14))

        info = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER)
        info.pack(fill="x", padx=20, pady=(0, 10))

        rows = [
            ("Cashier",       t["full_name"] or t["username"]),
            ("Payment",       t["payment_method"]),
            ("Amount Paid",   f"₱{t['amount_paid']:.2f}"),
            ("Change",        f"₱{t['change_due']:.2f}"),
            ("Total",         f"₱{t['total']:.2f}"),
        ]
        for i, (label, value) in enumerate(rows):
            if i > 0:
                ctk.CTkFrame(info, height=1, fg_color=BORDER).pack(fill="x", padx=14)

            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=8)

            ctk.CTkLabel(row, text=label,
                         font=font_bold(11),
                         text_color=FG_SECONDARY,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(value), anchor="e",
                         font=font_bold(12),
                         text_color=FG_PRIMARY).pack(side="right")

        ctk.CTkLabel(self, text="Items Purchased",
                     font=font_bold(13),
                     text_color=FG_PRIMARY).pack(pady=(10, 4))

        items_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                  corner_radius=12,
                                  border_width=1,
                                  border_color=BORDER)
        items_card.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        lines = ctk.CTkScrollableFrame(items_card, fg_color="transparent")
        lines.pack(fill="both", expand=True, padx=8, pady=8)

        header = ctk.CTkFrame(lines, fg_color="transparent")
        header.pack(fill="x", pady=(2, 6))
        for text, width in [("Item", 220), ("Qty", 60),
                            ("Price", 100), ("Subtotal", 110)]:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

        items = ReportController.transaction_items(t["transaction_id"])
        for i, it in enumerate(items):
            bg = BG_ROW_ALT if i % 2 else "transparent"
            row = ctk.CTkFrame(lines, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=1)

            ctk.CTkLabel(row, text=it["product_name"],
                         width=220, anchor="w",
                         font=font(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3, pady=6)
            ctk.CTkLabel(row, text=f"×{it['quantity']}",
                         width=60, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=f"₱{it['price']:.2f}",
                         width=100, anchor="w",
                         font=font(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=f"₱{it['subtotal']:.2f}",
                         width=110, anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)

        ctk.CTkButton(self, text="Close", width=140, height=38,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self.destroy).pack(pady=(6, 16))