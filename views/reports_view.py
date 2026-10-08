# ─────────────────────────────────────────────
# REPORTS TAB (embedded inside SalesView)
# ─────────────────────────────────────────────

from tkinter import messagebox
from datetime import datetime, timedelta

import customtkinter as ctk

from utils_pkg.pdf_export import export_sales_report
from controllers.report_controller import ReportController
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BG_INPUT, BG_ROW_ALT, BORDER,
    FG_PRIMARY, FG_SECONDARY, FG_MUTED,
    BRAND_GREEN,
    ACCENT, ACCENT_HOVER,
    SUCCESS, DANGER,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


class ReportsTab(ctk.CTkFrame):

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user

        self.date_from = ""
        self.date_to = ""
        self.search_query = ""
        self.payment_filter = "All"

        self.active_range_button = None
        self._programmatic_set = False

        self._build()
        self._refresh()

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        sub_header = ctk.CTkFrame(self, fg_color="transparent")
        sub_header.pack(fill="x", padx=20, pady=(10, 10))

        ctk.CTkLabel(sub_header,
                     text="Summary and top selling products",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(side="left")

        # ═════════════════════════════════════════
        # SUMMARY CARD
        # ═════════════════════════════════════════

        summary_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                    corner_radius=12,
                                    border_width=1,
                                    border_color=BORDER,
                                    height=110)
        summary_card.pack(fill="x", padx=20, pady=(0, 10))
        summary_card.pack_propagate(False)

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

        ctk.CTkFrame(summary_card, width=1, fg_color=BORDER).pack(
            side="left", fill="y", pady=14)

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

        ctk.CTkFrame(summary_card, width=1, fg_color=BORDER).pack(
            side="left", fill="y", pady=14)

        right_stat = ctk.CTkFrame(summary_card, fg_color="transparent",
                                  width=260)
        right_stat.pack(side="left", fill="y", padx=20, pady=14)
        right_stat.pack_propagate(False)

        ctk.CTkLabel(right_stat, text="PAYMENT BREAKDOWN",
                     font=font_bold(10),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x")

        cash_row = ctk.CTkFrame(right_stat, fg_color="transparent")
        cash_row.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(cash_row, text="Cash",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left")
        self.cash_total_label = ctk.CTkLabel(cash_row, text="₱0.00",
                                             font=font_bold(12),
                                             text_color=SUCCESS)
        self.cash_total_label.pack(side="right")

        gcash_row = ctk.CTkFrame(right_stat, fg_color="transparent")
        gcash_row.pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(gcash_row, text="GCash",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left")
        self.gcash_total_label = ctk.CTkLabel(gcash_row, text="₱0.00",
                                              font=font_bold(12),
                                              text_color=ACCENT)
        self.gcash_total_label.pack(side="right")

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

        row1 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(row1, text="Search",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        self.search_e = ctk.CTkEntry(
            row1,
            placeholder_text="Search by product name...",
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

        ctk.CTkButton(row1, text="Export PDF", width=120, height=36,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._export_pdf).pack(side="right", padx=(0, 6))

        ctk.CTkButton(row1, text="Refresh", width=100, height=36,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._refresh).pack(side="right")

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

        self.count_label = ctk.CTkLabel(row2, text="",
                                        font=font_bold(11),
                                        text_color=FG_SECONDARY)
        self.count_label.pack(side="right", padx=(0, 4))

        # ═════════════════════════════════════════
        # TOP SELLING PRODUCTS CARD
        # ═════════════════════════════════════════

        top_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                corner_radius=12,
                                border_width=1,
                                border_color=BORDER)
        top_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        top_header = ctk.CTkFrame(top_card, fg_color="transparent")
        top_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(top_header, text="TOP SELLING PRODUCTS",
                     font=font_bold(13),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(side="left")

        ctk.CTkLabel(top_header, text="Top 5",
                     font=font_bold(11),
                     text_color=FG_MUTED,
                     anchor="e").pack(side="right")

        ctk.CTkFrame(top_card, height=1, fg_color=BORDER).pack(
            fill="x", padx=16)

        self.list_frame = ctk.CTkScrollableFrame(top_card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    # ─────────────────────────────────────────────
    # EXPORT PDF
    # ─────────────────────────────────────────────

    def _export_pdf(self):
        try:
            summary = ReportController.summary(
                date_from=self.date_from or None,
                date_to=self.date_to or None,
            )
            products = ReportController.top_selling_products(
                date_from=self.date_from or None,
                date_to=self.date_to or None,
                search=self.search_query or None,
                payment_method=self.payment_filter,
                limit=5,
            )
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not fetch data:\n{e}")
            return

        summary_dict = dict(summary) if summary else {}

        exporter = (self.user.get("full_name")
                    or self.user.get("username")
                    or "-")

        ok, result = export_sales_report(
            summary=summary_dict,
            top_products=products,
            date_from=self.date_from or None,
            date_to=self.date_to or None,
            payment_filter=self.payment_filter,
            exporter_name=exporter,
            parent_window=self.winfo_toplevel(),
        )

        if ok:
            messagebox.showinfo("Export Complete",
                                f"PDF saved to:\n{result}")
        elif result != "Cancelled.":
            messagebox.showerror("Export Failed", result)

    # ─────────────────────────────────────────────
    # FILTERS
    # ─────────────────────────────────────────────

    def _on_search_change(self, *args):
        self.search_query = self.search_var.get().strip().lower()
        self._refresh()

    def _clear_search(self):
        self.search_var.set("")

    def _on_payment_change(self, choice):
        self.payment_filter = choice
        self._refresh()

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
        self._refresh()

    def _is_valid_date(self, text):
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return True
        except ValueError:
            return False

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

    def _set_dates_programmatically(self, d_from, d_to, button):
        self._programmatic_set = True
        self.date_from_var.set(d_from)
        self.date_to_var.set(d_to)
        self._programmatic_set = False

        self.date_from = d_from
        self.date_to = d_to
        self._highlight_button(button)
        self._refresh()

    # ─────────────────────────────────────────────
    # REFRESH
    # ─────────────────────────────────────────────

    def _refresh(self):
        try:
            summary = ReportController.summary(
                date_from=self.date_from or None,
                date_to=self.date_to or None,
            )
            self._update_summary(summary)

            top_products = ReportController.top_selling_products(
                date_from=self.date_from or None,
                date_to=self.date_to or None,
                search=self.search_query or None,
                payment_method=self.payment_filter,
                limit=5,
            )
            self._render_top_products(top_products)

        except Exception as e:
            import traceback
            traceback.print_exc()

            for w in self.list_frame.winfo_children():
                w.destroy()
            ctk.CTkLabel(self.list_frame,
                         text=f"Error loading reports:\n{e}",
                         font=font(11),
                         text_color=DANGER,
                         justify="left").pack(pady=20)

            self.total_sales_label.configure(text="—")
            self.txn_count_label.configure(text="—")
            self.cash_total_label.configure(text="—")
            self.gcash_total_label.configure(text="—")

    def _update_summary(self, summary):
        total_sales = summary["total_sales"] if summary else 0
        count = summary["count"] if summary else 0
        cash_total = summary["cash_total"] if summary else 0
        gcash_total = summary["gcash_total"] if summary else 0

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
    # RENDER TOP PRODUCTS
    # ─────────────────────────────────────────────

    def _render_top_products(self, products):
        for w in self.list_frame.winfo_children():
            w.destroy()

        if not products:
            ctk.CTkLabel(self.list_frame,
                         text="No sales data available for the selected period.",
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            self.count_label.configure(text="")
            return

        self.count_label.configure(text=f"{len(products)} product(s)")

        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))

        cols = [
            ("#",              30),
            ("Product",        260),
            ("Code",           100),
            ("Units Sold",     90),
            ("Cost",           85),
            ("Price",          85),
            ("Profit",         100),
            ("Revenue",        110),
        ]
        for text, width in cols:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

        for i, p in enumerate(products):
            bg = BG_ROW_ALT if i % 2 else BG_CARD
            row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=1)

            display = " ".join(
                part for part in (p.get("brand"), p["product_name"], p.get("size"))
                if part
            )

            profit = p.get("profit", 0)
            if profit > 0:
                profit_color = SUCCESS
            elif profit < 0:
                profit_color = DANGER
            else:
                profit_color = FG_MUTED

            ctk.CTkLabel(row, text=str(i + 1),
                         width=30, anchor="w",
                         font=font_bold(11),
                         text_color=FG_MUTED).pack(side="left", padx=3, pady=6)

            ctk.CTkLabel(row, text=display,
                         width=260, anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=p["product_code"],
                         width=100, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=f"{p['units_sold']:,}",
                         width=90, anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=f"₱{p['avg_cost']:.2f}",
                         width=85, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=f"₱{p['avg_price']:.2f}",
                         width=85, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=f"₱{profit:.2f}",
                         width=100, anchor="w",
                         font=font_bold(11),
                         text_color=profit_color).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=f"₱{p['revenue']:,.2f}",
                         width=110, anchor="w",
                         font=font_bold(12),
                         text_color=ACCENT).pack(side="left", padx=3)