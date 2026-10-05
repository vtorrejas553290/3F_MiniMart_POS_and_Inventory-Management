# ─────────────────────────────────────────────
# DASHBOARD VIEW (KPIs + Profit Today + Low Stock)
# ─────────────────────────────────────────────

import customtkinter as ctk

from controllers.dashboard_controller import DashboardController
from controllers.auth_controller import AuthController
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BG_INPUT, BG_ROW_ALT, BORDER,
    FG_PRIMARY, FG_SECONDARY, FG_MUTED,
    BRAND_GREEN, BRAND_YELLOW,
    ACCENT, ACCENT_HOVER, SUCCESS, DANGER, DANGER_HOVER,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


# ─────────────────────────────────────────────
# DASHBOARD VIEW
# ─────────────────────────────────────────────

class DashboardView(ctk.CTkFrame):

    PAGE_SIZE = 6

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user
        self.on_navigate = None

        self.lowstock_page = 1
        self.lowstock_total_pages = 1

        self._build()
        self._load()

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        # ═════════════════════════════════════════
        # HEADER
        # ═════════════════════════════════════════

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box,
                     text=f"Welcome back, {self.user['full_name']}",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="Here's an overview of your store today",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ═════════════════════════════════════════
        # KPI ROW (4 clickable cards)
        # ═════════════════════════════════════════

        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", padx=20, pady=(0, 10))

        self.sales_card = self._make_kpi_card(
            kpi_row, "TODAY'S SALES", "₱0.00", ACCENT,
            command=lambda: self._go_to_sales("Reports"),
        )
        self.txn_card = self._make_kpi_card(
            kpi_row, "TRANSACTIONS", "0", FG_PRIMARY,
            command=lambda: self._go_to_sales("Transactions"),
        )
        self.lowstock_card = self._make_kpi_card(
            kpi_row, "LOW STOCK", "0", "#D97706",
            command=self._go_to_inventory,
        )
        self.expiring_card = self._make_kpi_card(
            kpi_row, "EXPIRING SOON", "0", "#D97706",
            command=self._go_to_inventory,
        )

        # ═════════════════════════════════════════
        # TWO PANELS
        # ═════════════════════════════════════════

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # ---- LEFT: Profit Today ----
        profit_panel = ctk.CTkFrame(body, fg_color=BG_CARD,
                                    corner_radius=12,
                                    border_width=1,
                                    border_color=BORDER)
        profit_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        profit_header = ctk.CTkFrame(profit_panel, fg_color="transparent")
        profit_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(profit_header, text="Profit Today",
                     font=font_bold(14),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(side="left")

        # ---- Big profit number ----
        profit_body = ctk.CTkFrame(profit_panel, fg_color="transparent")
        profit_body.pack(fill="x", padx=20, pady=(6, 10))

        ctk.CTkLabel(profit_body, text="TOTAL PROFIT",
                     font=font_bold(10),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x")

        self.profit_total_label = ctk.CTkLabel(
            profit_body, text="₱0.00",
            font=font_bold(34),
            text_color=SUCCESS,
            anchor="w",
        )
        self.profit_total_label.pack(fill="x", pady=(2, 0))

        self.profit_sub_label = ctk.CTkLabel(
            profit_body, text="from 0 transactions",
            font=font(11),
            text_color=FG_MUTED,
            anchor="w",
        )
        self.profit_sub_label.pack(fill="x", pady=(2, 0))

        # ---- Divider ----
        ctk.CTkFrame(profit_panel, height=1, fg_color=BORDER).pack(
            fill="x", padx=16, pady=(6, 4))

        # ---- Breakdown rows ----
        breakdown = ctk.CTkFrame(profit_panel, fg_color="transparent")
        breakdown.pack(fill="x", padx=16, pady=(6, 16))

        self.cash_profit_label = self._make_breakdown_row(
            breakdown, "Cash profit", "₱0.00", SUCCESS,
        )
        self.gcash_profit_label = self._make_breakdown_row(
            breakdown, "GCash profit", "₱0.00", ACCENT,
        )
        self.revenue_label = self._make_breakdown_row(
            breakdown, "Revenue", "₱0.00", FG_PRIMARY,
        )
        self.cost_label = self._make_breakdown_row(
            breakdown, "Cost of goods", "₱0.00", FG_SECONDARY,
        )

        # ---- RIGHT: Low Stock Alerts ----
        right = ctk.CTkFrame(body, fg_color=BG_CARD,
                             corner_radius=12,
                             border_width=1,
                             border_color=BORDER)
        right.pack(side="right", fill="both", expand=True)

        right_header = ctk.CTkFrame(right, fg_color="transparent")
        right_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(right_header, text="Low Stock Alerts",
                     font=font_bold(14),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(side="left")

        ctk.CTkButton(right_header, text="View All",
                      width=90, height=30,
                      corner_radius=8,
                      font=font_bold(11),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._go_to_inventory
                      ).pack(side="right")

        self.lowstock_frame = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.lowstock_frame.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        self.lowstock_pager = self._make_pager(right, "lowstock")

    # ─────────────────────────────────────────────
    # KPI CARD BUILDER
    # ─────────────────────────────────────────────

    def _make_kpi_card(self, parent, label, value, value_color, command):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER,
                            height=100)
        card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        label_widget = ctk.CTkLabel(inner, text=label,
                                    font=font_bold(10),
                                    text_color=FG_SECONDARY,
                                    anchor="w")
        label_widget.pack(fill="x")

        value_label = ctk.CTkLabel(inner, text=value,
                                   font=font_bold(24),
                                   text_color=value_color,
                                   anchor="w")
        value_label.pack(fill="x", pady=(4, 0))

        for w in (card, inner, label_widget, value_label):
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>", lambda e, c=card:
                   c.configure(fg_color="#EAF0FF"))
            w.bind("<Leave>", lambda e, c=card:
                   c.configure(fg_color=BG_CARD))
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass

        return value_label

    # ─────────────────────────────────────────────
    # BREAKDOWN ROW HELPER
    # ─────────────────────────────────────────────

    def _make_breakdown_row(self, parent, label, value, value_color):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)

        ctk.CTkLabel(row, text=label,
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(side="left")

        value_label = ctk.CTkLabel(row, text=value,
                                   font=font_bold(12),
                                   text_color=value_color,
                                   anchor="e")
        value_label.pack(side="right")

        return value_label

    # ─────────────────────────────────────────────
    # PAGER
    # ─────────────────────────────────────────────

    def _make_pager(self, parent, pager_key):
        pager = ctk.CTkFrame(parent, fg_color="transparent")
        pager.pack(fill="x", padx=12, pady=(0, 12))

        prev_btn = ctk.CTkButton(
            pager, text="‹ Prev",
            width=80, height=30,
            corner_radius=8,
            font=font_bold(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=lambda: self._change_page(pager_key, -1),
        )
        prev_btn.pack(side="left")

        page_label = ctk.CTkLabel(pager, text="Page 1 of 1",
                                  font=font_bold(11),
                                  text_color=FG_SECONDARY)
        page_label.pack(side="left", fill="x", expand=True)

        next_btn = ctk.CTkButton(
            pager, text="Next ›",
            width=80, height=30,
            corner_radius=8,
            font=font_bold(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=lambda: self._change_page(pager_key, +1),
        )
        next_btn.pack(side="right")

        return {"prev": prev_btn, "next": next_btn, "label": page_label}

    def _change_page(self, pager_key, delta):
        if pager_key == "lowstock":
            new_page = self.lowstock_page + delta
            if 1 <= new_page <= self.lowstock_total_pages:
                self.lowstock_page = new_page
                self._render_low_stock()

    # ─────────────────────────────────────────────
    # NAVIGATION
    # ─────────────────────────────────────────────

    def _go_to_sales(self, tab_name="Transactions"):
        if callable(self.on_navigate):
            self.on_navigate("sales")

    def _go_to_inventory(self):
        if callable(self.on_navigate):
            self.on_navigate("inventory")

    # ─────────────────────────────────────────────
    # LOAD
    # ─────────────────────────────────────────────

    def _load(self):
        stats = DashboardController.get_stats()

        self.sales_card.configure(
            text=f"₱{stats.get('total_sales_today', 0):,.2f}"
        )
        self.txn_card.configure(
            text=f"{stats.get('txn_count_today', 0):,}"
        )

        low_count = stats.get("low_stock_count", 0)
        self.lowstock_card.configure(
            text=f"{low_count:,}",
            text_color=("#D97706" if low_count > 0 else FG_PRIMARY),
        )

        expiring = stats.get("expiring_soon_count", 0)
        expired = stats.get("expired_count", 0)
        self.expiring_card.configure(
            text=f"{expiring:,}",
            text_color=(DANGER if expired > 0 else
                        "#D97706" if expiring > 0 else FG_PRIMARY),
        )

        # ---- Profit panel ----
        p = DashboardController.get_profit_today()
        profit = p["profit"]

        profit_color = SUCCESS if profit >= 0 else DANGER
        self.profit_total_label.configure(
            text=f"₱{profit:,.2f}",
            text_color=profit_color,
        )
        self.profit_sub_label.configure(
            text=f"from {p['txn_count']:,} transaction(s)"
        )
        self.cash_profit_label.configure(text=f"₱{p['cash_profit']:,.2f}")
        self.gcash_profit_label.configure(text=f"₱{p['gcash_profit']:,.2f}")
        self.revenue_label.configure(text=f"₱{p['revenue']:,.2f}")
        self.cost_label.configure(text=f"₱{p['cost']:,.2f}")

        self._render_low_stock()

    # ─────────────────────────────────────────────
    # LOW STOCK
    # ─────────────────────────────────────────────

    def _render_low_stock(self):
        for w in self.lowstock_frame.winfo_children():
            w.destroy()

        rows = DashboardController.low_stock_products(limit=500)
        total = len(rows)
        self.lowstock_total_pages = max(
            1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        )
        if self.lowstock_page > self.lowstock_total_pages:
            self.lowstock_page = self.lowstock_total_pages

        start = (self.lowstock_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_rows = rows[start:end]

        if not page_rows:
            ctk.CTkLabel(self.lowstock_frame,
                         text="All products are well-stocked.",
                         font=font(11),
                         text_color=FG_MUTED).pack(pady=30)
            self._update_pager(self.lowstock_pager, 1, 1)
            return

        # ---- Header ----
        header = ctk.CTkFrame(self.lowstock_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))

        for text, width in [
            ("Product",    180),
            ("Category",   90),
            ("Stock",      55),
            ("Min",        45),
        ]:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

        # ---- Rows ----
        for i, p in enumerate(page_rows):
            bg = BG_ROW_ALT if i % 2 else BG_CARD

            row = ctk.CTkFrame(self.lowstock_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            display = " ".join(
                part for part in (p.get("brand"), p["name"], p.get("size"))
                if part
            )

            ctk.CTkLabel(row, text=display,
                         width=180, anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=4, pady=6)

            ctk.CTkLabel(row, text=p["category_name"] or "-",
                         width=90, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

            stock = p["stock_qty"]
            if stock <= 0:
                stock_text, stock_color = "Out", DANGER
            else:
                stock_text, stock_color = f"{stock}", "#D97706"

            ctk.CTkLabel(row, text=stock_text,
                         width=55, anchor="w",
                         font=font_bold(11),
                         text_color=stock_color).pack(side="left", padx=4)

            ctk.CTkLabel(row, text=str(p["low_stock_level"] or 0),
                         width=45, anchor="w",
                         font=font(11),
                         text_color=FG_MUTED).pack(side="left", padx=4)

        self._update_pager(self.lowstock_pager,
                           self.lowstock_page, self.lowstock_total_pages)

    # ─────────────────────────────────────────────
    # PAGER STATE
    # ─────────────────────────────────────────────

    def _update_pager(self, pager, current, total):
        pager["label"].configure(text=f"Page {current} of {total}")

        if current <= 1:
            pager["prev"].configure(state="disabled",
                                    fg_color=BG_INPUT,
                                    text_color=FG_MUTED)
        else:
            pager["prev"].configure(state="normal",
                                    fg_color=NEUTRAL,
                                    text_color=NEUTRAL_TEXT)

        if current >= total:
            pager["next"].configure(state="disabled",
                                    fg_color=BG_INPUT,
                                    text_color=FG_MUTED)
        else:
            pager["next"].configure(state="normal",
                                    fg_color=NEUTRAL,
                                    text_color=NEUTRAL_TEXT)