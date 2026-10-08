# ─────────────────────────────────────────────
# SALES VIEW (tabs: Transactions | Reports)
# ─────────────────────────────────────────────

import customtkinter as ctk

from controllers.auth_controller import AuthController
from views.transactions_view import TransactionsTab
from views.reports_view import ReportsTab
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BORDER,
    FG_PRIMARY, FG_SECONDARY, FG_MUTED,
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

        # ---- Tab button references (for active state styling) ----
        self._tab_buttons = {}
        self._tab_underlines = {}

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
            tab_wrapper = ctk.CTkFrame(self, fg_color="transparent")
            tab_wrapper.pack(fill="x", padx=20, pady=(0, 6))

            tab_bar = ctk.CTkFrame(tab_wrapper, fg_color="transparent")
            tab_bar.pack(fill="x")

            # ---- Tab buttons ----
            self._make_tab_button(tab_bar, "Transactions")
            self._make_tab_button(tab_bar, "Reports")

            # ---- Full-width underline base ----
            underline_base = ctk.CTkFrame(
                tab_wrapper, height=1, fg_color=BORDER
            )
            underline_base.pack(fill="x", pady=(0, 0))

        # ---- Content frame ----
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)

        # ---- Load default tab ----
        self._show_tab("Transactions")

    def _make_tab_button(self, parent, name):
        """Create a single tab button with an underline indicator."""
        btn = ctk.CTkButton(
            parent,
            text=name,
            width=140,
            height=38,
            corner_radius=8,
            font=font_bold(12),
            fg_color="transparent",
            hover_color=NEUTRAL,
            text_color=FG_SECONDARY,
            anchor="center",
            command=lambda n=name: self._on_tab_click(n),
        )
        btn.pack(side="left", padx=(0, 4))

        # ---- Underline (hidden by default) ----
        underline = ctk.CTkFrame(
            btn, height=3, corner_radius=2,
            fg_color=ACCENT,
        )

        self._tab_buttons[name] = btn
        self._tab_underlines[name] = underline

    # ─────────────────────────────────────────────
    # TAB SWITCHING
    # ─────────────────────────────────────────────

    def _on_tab_click(self, tab_name):
        self._show_tab(tab_name)

    def _set_active_tab(self, tab_name):
        """Update visual state of tab buttons."""
        for name, btn in self._tab_buttons.items():
            if name == tab_name:
                btn.configure(
                    text_color=FG_PRIMARY,
                    fg_color="transparent",
                    hover_color=NEUTRAL,
                )
                self._tab_underlines[name].place(
                    relx=0.5, rely=1.0, anchor="s",
                    relwidth=0.7,
                )
            else:
                btn.configure(
                    text_color=FG_MUTED,
                    fg_color="transparent",
                    hover_color=NEUTRAL,
                )
                self._tab_underlines[name].place_forget()

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

        # ---- Update tab styling ----
        if self.is_admin:
            self._set_active_tab(tab_name)