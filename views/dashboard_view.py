# ─────────────────────────────────────────────
# DASHBOARD VIEW (quick overview for the owner,
#                 with pagination for lists)
# ─────────────────────────────────────────────

import customtkinter as ctk

from controllers.dashboard_controller import DashboardController
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

    # ---- Pagination size ----
    PAGE_SIZE = 5

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user
        self.on_navigate = None

        # ---- Pagination state ----
        self.recent_page = 1
        self.recent_total_pages = 1

        self.lowstock_page = 1
        self.lowstock_total_pages = 1

        self._build()
        self._load()

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
        # STAT CARDS ROW
        # ═════════════════════════════════════════

        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=20, pady=(0, 10))

        self.sales_card    = self._make_stat_card(stats_row, "TODAY'S SALES",      "₱0.00", ACCENT)
        self.txn_card      = self._make_stat_card(stats_row, "TRANSACTIONS TODAY", "0",     FG_PRIMARY)
        self.products_card = self._make_stat_card(stats_row, "ACTIVE PRODUCTS",    "0",     BRAND_GREEN)
        self.lowstock_card = self._make_stat_card(stats_row, "LOW STOCK",          "0",     "#D97706")

        # ═════════════════════════════════════════
        # TWO COLUMNS
        # ═════════════════════════════════════════

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # ---- LEFT: Recent Transactions ----
        left = ctk.CTkFrame(body, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        left_header = ctk.CTkFrame(left, fg_color="transparent")
        left_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(left_header, text="Recent Transactions",
                     font=font_bold(14),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(side="left")

        ctk.CTkButton(left_header, text="View All",
                      width=90, height=30,
                      corner_radius=8,
                      font=font_bold(11),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=lambda: self._go_to("reports")
                      ).pack(side="right")

        # ---- Recent list ----
        self.recent_frame = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.recent_frame.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        # ---- Recent pagination controls ----
        self.recent_pager = self._make_pager(left, "recent")

        # ---- RIGHT: Low Stock ----
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
                      command=lambda: self._go_to("inventory")
                      ).pack(side="right")

        # ---- Low stock list ----
        self.lowstock_frame = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.lowstock_frame.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        # ---- Low stock pagination controls ----
        self.lowstock_pager = self._make_pager(right, "lowstock")

    # ─────────────────────────────────────────────
    # STAT CARD BUILDER
    # ─────────────────────────────────────────────

    def _make_stat_card(self, parent, label, value, value_color):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER,
                            height=100)
        card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        ctk.CTkLabel(inner, text=label,
                     font=font_bold(10),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x")

        value_label = ctk.CTkLabel(inner, text=value,
                                   font=font_bold(24),
                                   text_color=value_color,
                                   anchor="w")
        value_label.pack(fill="x", pady=(4, 0))

        return value_label

    # ─────────────────────────────────────────────
    # PAGER BUILDER
    # ─────────────────────────────────────────────

    def _make_pager(self, parent, pager_key):
        """
        Build a Prev / Next / page-indicator row.
        Returns a dict with the widgets so they can be updated later.
        """
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

        page_label = ctk.CTkLabel(
            pager, text="Page 1 of 1",
            font=font_bold(11),
            text_color=FG_SECONDARY,
        )
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

        return {
            "prev":  prev_btn,
            "next":  next_btn,
            "label": page_label,
        }

    # ─────────────────────────────────────────────
    # PAGE CHANGE
    # ─────────────────────────────────────────────

    def _change_page(self, pager_key, delta):
        if pager_key == "recent":
            new_page = self.recent_page + delta
            if 1 <= new_page <= self.recent_total_pages:
                self.recent_page = new_page
                self._render_recent_transactions()
        elif pager_key == "lowstock":
            new_page = self.lowstock_page + delta
            if 1 <= new_page <= self.lowstock_total_pages:
                self.lowstock_page = new_page
                self._render_low_stock()

    # ─────────────────────────────────────────────
    # NAVIGATION HELPER
    # ─────────────────────────────────────────────

    def _go_to(self, key):
        if callable(self.on_navigate):
            self.on_navigate(key)

    # ─────────────────────────────────────────────
    # LOAD DATA
    # ─────────────────────────────────────────────

    def _load(self):
        stats = DashboardController.get_stats()

        self.sales_card.configure(text=f"₱{stats['total_sales_today']:,.2f}")
        self.txn_card.configure(text=f"{stats['txn_count_today']:,}")
        self.products_card.configure(text=f"{stats['total_products']:,}")
        self.lowstock_card.configure(text=f"{stats['low_stock_count']:,}")

        self._render_recent_transactions()
        self._render_low_stock()

    # ─────────────────────────────────────────────
    # RECENT TRANSACTIONS (paginated)
    # ─────────────────────────────────────────────

    def _render_recent_transactions(self):
        for w in self.recent_frame.winfo_children():
            w.destroy()

        # ---- Fetch all, then slice ----
        rows = DashboardController.recent_transactions(limit=500)

        total = len(rows)
        self.recent_total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

        # ---- Clamp current page ----
        if self.recent_page > self.recent_total_pages:
            self.recent_page = self.recent_total_pages

        start = (self.recent_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_rows = rows[start:end]

        # ---- Empty state ----
        if not page_rows:
            ctk.CTkLabel(self.recent_frame,
                         text="No transactions yet.",
                         font=font(11),
                         text_color=FG_MUTED).pack(pady=30)
            self._update_pager(self.recent_pager, 1, 1)
            return

        # ---- Render rows ----
        for i, t in enumerate(page_rows):
            bg = BG_ROW_ALT if i % 2 else "transparent"

            row = ctk.CTkFrame(self.recent_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=f"#{t['transaction_id']}",
                         width=60, anchor="w",
                         font=font_bold(11),
                         text_color=ACCENT).pack(side="left", padx=(8, 4), pady=6)

            ctk.CTkLabel(row,
                         text=t["full_name"] or t["username"] or "-",
                         width=120, anchor="w",
                         font=font(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=4)

            pay_color = SUCCESS if t["payment_method"] == "Cash" else ACCENT
            ctk.CTkLabel(row, text=t["payment_method"],
                         width=70, anchor="w",
                         font=font_bold(11),
                         text_color=pay_color).pack(side="left", padx=4)

            ctk.CTkLabel(row, text=(t["created_at"] or "")[:16],
                         width=130, anchor="w",
                         font=font(10),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

            ctk.CTkLabel(row, text=f"₱{t['total']:.2f}",
                         width=80, anchor="e",
                         font=font_bold(12),
                         text_color=ACCENT).pack(side="right", padx=(4, 8))

        # ---- Update pager ----
        self._update_pager(self.recent_pager,
                           self.recent_page, self.recent_total_pages)

    # ─────────────────────────────────────────────
    # LOW STOCK (paginated)
    # ─────────────────────────────────────────────

    def _render_low_stock(self):
        for w in self.lowstock_frame.winfo_children():
            w.destroy()

        # ---- Fetch all, then slice ----
        rows = DashboardController.low_stock_products(limit=500)

        total = len(rows)
        self.lowstock_total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

        # ---- Clamp current page ----
        if self.lowstock_page > self.lowstock_total_pages:
            self.lowstock_page = self.lowstock_total_pages

        start = (self.lowstock_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_rows = rows[start:end]

        # ---- Empty state ----
        if not page_rows:
            ctk.CTkLabel(self.lowstock_frame,
                         text="All products are well-stocked.",
                         font=font(11),
                         text_color=FG_MUTED).pack(pady=30)
            self._update_pager(self.lowstock_pager, 1, 1)
            return

        # ---- Render rows ----
        for i, p in enumerate(page_rows):
            bg = BG_ROW_ALT if i % 2 else "transparent"

            row = ctk.CTkFrame(self.lowstock_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=p["name"],
                         width=170, anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=(8, 4), pady=6)

            ctk.CTkLabel(row, text=p["category_name"] or "-",
                         width=90, anchor="w",
                         font=font(10),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

            stock = p["stock_qty"]
            if stock <= 0:
                stock_text = "Out"
                stock_color = DANGER
            else:
                stock_text = f"{stock}"
                stock_color = "#D97706"

            ctk.CTkLabel(row, text=stock_text,
                         width=50,
                         font=font_bold(11),
                         text_color=stock_color).pack(side="left", padx=4)

            ctk.CTkLabel(row, text=f"min {p['low_stock_level']}",
                         width=60, anchor="e",
                         font=font(10),
                         text_color=FG_MUTED).pack(side="right", padx=(4, 8))

        # ---- Update pager ----
        self._update_pager(self.lowstock_pager,
                           self.lowstock_page, self.lowstock_total_pages)

    # ─────────────────────────────────────────────
    # PAGER STATE UPDATE
    # ─────────────────────────────────────────────

    def _update_pager(self, pager, current, total):
        """Enable/disable Prev/Next and update the label."""
        pager["label"].configure(text=f"Page {current} of {total}")

        # ---- Prev button ----
        if current <= 1:
            pager["prev"].configure(
                state="disabled",
                fg_color=BG_INPUT,
                text_color=FG_MUTED,
            )
        else:
            pager["prev"].configure(
                state="normal",
                fg_color=NEUTRAL,
                text_color=NEUTRAL_TEXT,
            )

        # ---- Next button ----
        if current >= total:
            pager["next"].configure(
                state="disabled",
                fg_color=BG_INPUT,
                text_color=FG_MUTED,
            )
        else:
            pager["next"].configure(
                state="normal",
                fg_color=NEUTRAL,
                text_color=NEUTRAL_TEXT,
            )