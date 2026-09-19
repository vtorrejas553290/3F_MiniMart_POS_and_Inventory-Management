# ─────────────────────────────────────────────
# ACTIVITY LOG VIEW (softened 3F MiniMart branding)
# ─────────────────────────────────────────────

import customtkinter as ctk
from datetime import datetime, timedelta

from controllers.activity_log_controller import ActivityLogController
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BG_INPUT, BG_ROW_ALT, BORDER,
    FG_PRIMARY, FG_SECONDARY, FG_MUTED,
    BRAND_GREEN, BRAND_BLUE, BRAND_YELLOW,
    ACCENT, ACCENT_HOVER, NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


# ─────────────────────────────────────────────
# ACTIVITY LOG VIEW
# ─────────────────────────────────────────────

class ActivityLogView(ctk.CTkFrame):

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

        # ---- Active quick-range button ----
        self.active_range_button = None
        self._programmatic_set = False

        self._build()
        self._refresh_logs()

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        # ═════════════════════════════════════════
        # PAGE HEADER
        # ═════════════════════════════════════════

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header_frame, text="Activity Logs",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(header_frame,
                     text="Track every action taken in the system",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ═════════════════════════════════════════
        # FILTER CARD
        # ═════════════════════════════════════════

        filter_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                   corner_radius=12,
                                   border_width=1,
                                   border_color=BORDER)
        filter_card.pack(fill="x", padx=20, pady=(0, 10))

        # ---- Row 1: search ----
        row1 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(row1, text="Search",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        self.search_e = ctk.CTkEntry(
            row1,
            placeholder_text="Search by user, action, details...",
            textvariable=self.search_var,
            width=360,
            height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
        )
        self.search_e.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row1, text="✕", width=36, height=36,
            corner_radius=8,
            font=font(13),
            fg_color=NEUTRAL,
            hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._clear_search,
        ).pack(side="left", padx=(0, 20))

        # ---- Refresh button ----
        ctk.CTkButton(
            row1, text="Refresh", width=100, height=36,
            corner_radius=8,
            font=font_bold(12),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._refresh_logs,
        ).pack(side="right")

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
            fg_color=NEUTRAL,
            hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._range_today,
        )
        self.btn_today.pack(side="left", padx=2)

        self.btn_7days = ctk.CTkButton(
            row2, text="Last 7 Days", width=100, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL,
            hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._range_7_days,
        )
        self.btn_7days.pack(side="left", padx=2)

        self.btn_month = ctk.CTkButton(
            row2, text="This Month", width=100, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL,
            hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._range_this_month,
        )
        self.btn_month.pack(side="left", padx=2)

        self.btn_clear = ctk.CTkButton(
            row2, text="Clear Dates", width=100, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL,
            hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._clear_dates,
        )
        self.btn_clear.pack(side="left", padx=2)

        # ---- Results count ----
        self.count_label = ctk.CTkLabel(
            row2, text="",
            font=font_bold(11),
            text_color=FG_SECONDARY,
        )
        self.count_label.pack(side="right", padx=(0, 4))

        # ═════════════════════════════════════════
        # LIST CARD
        # ═════════════════════════════════════════

        list_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                 corner_radius=12,
                                 border_width=1,
                                 border_color=BORDER)
        list_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.list_frame = ctk.CTkScrollableFrame(
            list_card,
            fg_color="transparent",
        )
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    # ─────────────────────────────────────────────
    # FILTERS — SEARCH
    # ─────────────────────────────────────────────

    def _on_search_change(self, *args):
        self.search_query = self.search_var.get().strip().lower()
        self._refresh_logs()

    def _clear_search(self):
        self.search_var.set("")

    # ─────────────────────────────────────────────
    # QUICK-RANGE BUTTON HIGHLIGHT
    # ─────────────────────────────────────────────

    def _highlight_button(self, button):
        # ---- Reset previous ----
        if self.active_range_button is not None:
            self.active_range_button.configure(
                fg_color=NEUTRAL,
                text_color=NEUTRAL_TEXT,
            )
        # ---- Highlight new ----
        if button is not None:
            button.configure(
                fg_color=BRAND_GREEN,
                text_color="#FFFFFF",
            )
        self.active_range_button = button

    def _clear_button_highlight(self):
        if self.active_range_button is not None:
            self.active_range_button.configure(
                fg_color=NEUTRAL,
                text_color=NEUTRAL_TEXT,
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
        self._refresh_logs()

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
        self._refresh_logs()

    # ─────────────────────────────────────────────
    # REFRESH
    # ─────────────────────────────────────────────

    def _refresh_logs(self):
        rows = ActivityLogController.list_filtered(
            date_from=self.date_from or None,
            date_to=self.date_to or None,
            search=self.search_query or None,
        )
        self._render(rows)

    # ─────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────

    def _render(self, logs):
        for w in self.list_frame.winfo_children():
            w.destroy()

        self.count_label.configure(text=f"{len(logs)} log(s)")

        # ---- Header row ----
        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))

        cols = [
            ("Date / Time", 160),
            ("User",        120),
            ("Action",      160),
            ("Details",     420),
        ]
        for text, width in cols:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=6)

        # ---- Empty state ----
        if not logs:
            ctk.CTkLabel(self.list_frame,
                         text="No logs match your filters.",
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            return

        # ---- Log rows (with zebra striping) ----
        for i, log in enumerate(logs):
            bg = BG_ROW_ALT if i % 2 else BG_CARD

            row = ctk.CTkFrame(self.list_frame, fg_color=bg,
                               corner_radius=6)
            row.pack(fill="x", pady=2)

            # ---- Date / Time ----
            ctk.CTkLabel(row, text=log["created_at"],
                         width=160, anchor="w",
                         font=font(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=6, pady=6)

            # ---- User ----
            ctk.CTkLabel(row, text=log["username"] or "-",
                         width=120, anchor="w",
                         font=font(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=6)

            # ---- Action (color-coded) ----
            action = log["action"] or ""
            action_color = self._action_color(action)
            ctk.CTkLabel(row, text=action,
                         width=160, anchor="w",
                         font=font_bold(11),
                         text_color=action_color).pack(side="left", padx=6)

            # ---- Details ----
            ctk.CTkLabel(row, text=log["details"] or "",
                         width=420, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=6)

    # ─────────────────────────────────────────────
    # ACTION COLOR MAP
    # ─────────────────────────────────────────────

    @staticmethod
    def _action_color(action):
        """Return a color for each action type."""
        a = action.upper()

        # ---- Success / create ----
        if a in ("LOGIN", "SALE", "ADD_PRODUCT", "ADD_SUPPLIER",
                 "ADD_CATEGORY", "ADD_SUPPLIER_CATEGORY",
                 "CREATE_PURCHASE", "RECEIVE_PURCHASE",
                 "RESTOCK_PRODUCT"):
            return BRAND_GREEN

        # ---- Warning / modify ----
        if a in ("UPDATE_PRODUCT", "UPDATE_SUPPLIER", "UPDATE_CATEGORY",
                 "UPDATE_SUPPLIER_CATEGORY", "VIEW_REPORT"):
            return "#D97706"     # ---- amber ----

        # ---- Danger / archive ----
        if a in ("ARCHIVE_PRODUCT", "ARCHIVE_SUPPLIER",
                 "CANCEL_PURCHASE", "LOGOUT"):
            return "#DC2626"     # ---- red ----

        # ---- Default ----
        return FG_SECONDARY