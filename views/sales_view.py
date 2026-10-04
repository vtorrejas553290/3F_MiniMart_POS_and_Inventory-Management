# ─────────────────────────────────────────────
# SALES VIEW (tabs: Transactions | Reports)
# ─────────────────────────────────────────────

import customtkinter as ctk

from controllers.auth_controller import AuthController
from views.transactions_view import TransactionsTab
from views.reports_view import ReportsTab
from config import (
    font, font_bold,
    BG_MAIN, FG_PRIMARY, FG_SECONDARY,
    ACCENT, ACCENT_HOVER,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


class SalesView(ctk.CTkFrame):

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user
        self.is_admin = AuthController.is_admin()

        # ---- Track current tab content ----
        self.current_tab = None
        self.tab_content = None

        self._build()

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        # ---- Page header ----
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box, text="Sales",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="Transaction history and sales summary",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ═════════════════════════════════════════
        # TAB BAR — admin only (staff sees just Transactions)
        # ═════════════════════════════════════════

        if self.is_admin:
            tab_bar = ctk.CTkFrame(self, fg_color="transparent")
            tab_bar.pack(fill="x", padx=20, pady=(0, 6))

            self.segmented = ctk.CTkSegmentedButton(
                tab_bar,
                values=["Transactions", "Reports"],
                font=font_bold(12),
                height=36,
                corner_radius=8,
                selected_color=ACCENT,
                selected_hover_color=ACCENT_HOVER,
                unselected_color=NEUTRAL,
                unselected_hover_color=NEUTRAL_HOVER,
                text_color=NEUTRAL_TEXT,
                command=self._on_tab_change,
            )
            self.segmented.pack(side="left")
            self.segmented.set("Transactions")

        # ---- Content frame ----
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)

        # ---- Load default tab ----
        self._show_tab("Transactions")

    # ─────────────────────────────────────────────
    # TAB SWITCHING
    # ─────────────────────────────────────────────

    def _on_tab_change(self, tab_name):
        self._show_tab(tab_name)

    def _show_tab(self, tab_name):
        # Don't reload if same tab
        if self.current_tab == tab_name and self.tab_content is not None:
            return

        # Clear old content
        for w in self.content_frame.winfo_children():
            w.destroy()

        # Block Reports for non-admins (shouldn't happen — tab not shown)
        if tab_name == "Reports" and not self.is_admin:
            tab_name = "Transactions"

        # Instantiate the tab
        if tab_name == "Reports":
            self.tab_content = ReportsTab(self.content_frame, self.user)
        else:
            self.tab_content = TransactionsTab(self.content_frame, self.user)

        self.tab_content.pack(fill="both", expand=True)
        self.current_tab = tab_name