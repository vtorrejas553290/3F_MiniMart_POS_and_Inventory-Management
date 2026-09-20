# ─────────────────────────────────────────────
# MAIN WINDOW (softened 3F MiniMart branding + dashboard + users)
# ─────────────────────────────────────────────

import customtkinter as ctk
from tkinter import messagebox

from config import (
    APP_NAME, font, font_bold,
    BRAND_GREEN, BRAND_YELLOW,
    BG_MAIN, BG_SIDEBAR, BG_SIDEBAR_ITEM, BG_SIDEBAR_HOVER,
    FG_ON_BRAND, FG_SECONDARY,
    ACCENT, ACCENT_HOVER, DANGER, DANGER_HOVER,
)
from controllers.auth_controller import AuthController

from views.dashboard_view import DashboardView
from views.pos_view import POSView
from views.inventory_view import InventoryView
from views.supplier_view import SupplierView
from views.purchase_view import PurchaseView
from views.reports_view import ReportsView
from views.activity_log_view import ActivityLogView
from views.user_management_view import UserManagementView


class MainWindow(ctk.CTk):

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Dashboard")
        self.configure(fg_color=BG_MAIN)

        # ---- Maximize on open ----
        self.after(0, lambda: self.state("zoomed"))
        self.minsize(1000, 600)

        self.user = AuthController.get_current_user()
        self.nav_buttons = {}

        self._build()

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        # ═════════════════════════════════════════
        # SIDEBAR — deep navy
        # ═════════════════════════════════════════

        sidebar = ctk.CTkFrame(self, width=240, corner_radius=0,
                               fg_color=BG_SIDEBAR)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # ---- Brand (auto-sizing) ----
        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(24, 8))

        ctk.CTkLabel(brand, text="3F",
                     font=font_bold(30),
                     text_color=BRAND_GREEN).pack(side="left")

        ctk.CTkLabel(brand, text="MiniMart",
                     font=font(16),
                     text_color=FG_ON_BRAND).pack(side="left", padx=(6, 0))

        # ---- User card ----
        user_box = ctk.CTkFrame(sidebar, fg_color=BG_SIDEBAR_ITEM,
                                corner_radius=10)
        user_box.pack(fill="x", padx=14, pady=(12, 20))

        ctk.CTkLabel(user_box, text=self.user["full_name"],
                     font=font_bold(13),
                     text_color=FG_ON_BRAND,
                     anchor="w").pack(fill="x", padx=12, pady=(10, 0))

        role_text = self.user["role"].upper()
        role_color = BRAND_YELLOW if self.user["role"] == "admin" else BRAND_GREEN
        ctk.CTkLabel(user_box, text=role_text,
                     font=font_bold(10),
                     text_color=role_color,
                     anchor="w").pack(fill="x", padx=12, pady=(0, 10))

        # ---- Section label ----
        ctk.CTkLabel(sidebar, text="MENU",
                     font=font_bold(10),
                     text_color="#94A3B8",
                     anchor="w").pack(fill="x", padx=22, pady=(4, 4))

        # ---- Navigation (role-based) ----
        self._nav_button(sidebar, "dashboard", "🏠   Dashboard",        self._show_dashboard)
        self._nav_button(sidebar, "pos",       "🛒   POS / Sales",       self._show_pos)
        self._nav_button(sidebar, "inventory", "📦   Inventory",         self._show_inventory)
        self._nav_button(sidebar, "suppliers", "🏢   Suppliers",         self._show_suppliers)
        self._nav_button(sidebar, "purchases", "📋   Purchase Records",  self._show_purchases)
        self._nav_button(sidebar, "reports",   "📊   Reports",           self._show_reports)

        if AuthController.is_admin():
            self._nav_button(sidebar, "users", "👤   User Management",  self._show_users)
            self._nav_button(sidebar, "logs",  "📝   Activity Logs",     self._show_logs)

        # ---- Logout ----
        ctk.CTkButton(
            sidebar,
            text="Logout",
            font=font_bold(12),
            height=38,
            corner_radius=8,
            fg_color="transparent",
            hover_color=BG_SIDEBAR_ITEM,
            border_width=1,
            border_color="#475569",
            text_color=FG_ON_BRAND,
            command=self._logout,
        ).pack(side="bottom", padx=14, pady=20, fill="x")

        # ═════════════════════════════════════════
        # CONTENT AREA
        # ═════════════════════════════════════════

        self.content = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        # ---- Default view: Dashboard ----
        self._show_dashboard()
        if "dashboard" in self.nav_buttons:
            self.nav_buttons["dashboard"].configure(
                fg_color=BRAND_GREEN, text_color="#FFFFFF"
            )

    # ─────────────────────────────────────────────
    # NAV BUTTON
    # ─────────────────────────────────────────────

    def _nav_button(self, parent, key, text, command):
        btn = ctk.CTkButton(
            parent,
            text=text,
            font=font(13),
            anchor="w",
            height=42,
            corner_radius=8,
            fg_color="transparent",
            hover_color=BG_SIDEBAR_HOVER,
            text_color=FG_ON_BRAND,
            command=lambda: self._navigate(key, command),
        )
        btn.pack(fill="x", padx=10, pady=2)
        self.nav_buttons[key] = btn

    def _navigate(self, key, command):
        # ---- Reset all nav buttons ----
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color="transparent", text_color=FG_ON_BRAND)

        # ---- Highlight active ----
        if key in self.nav_buttons:
            self.nav_buttons[key].configure(
                fg_color=BRAND_GREEN, text_color="#FFFFFF"
            )

        # ---- Run view ----
        command()

    def _navigate_by_key(self, key):
        """Used by dashboard shortcuts to jump to another view."""
        mapping = {
            "dashboard": self._show_dashboard,
            "pos":       self._show_pos,
            "inventory": self._show_inventory,
            "suppliers": self._show_suppliers,
            "purchases": self._show_purchases,
            "reports":   self._show_reports,
            "users":     self._show_users,
            "logs":      self._show_logs,
        }
        if key in mapping:
            self._navigate(key, mapping[key])

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ─────────────────────────────────────────────
    # NAVIGATION HANDLERS
    # ─────────────────────────────────────────────

    def _show_dashboard(self):
        self._clear_content()
        view = DashboardView(self.content, self.user)
        view.on_navigate = self._navigate_by_key
        view.pack(fill="both", expand=True)

    def _show_pos(self):
        self._clear_content()
        POSView(self.content, self.user).pack(fill="both", expand=True)

    def _show_inventory(self):
        self._clear_content()
        InventoryView(self.content, self.user).pack(fill="both", expand=True)

    def _show_suppliers(self):
        self._clear_content()
        SupplierView(self.content, self.user).pack(fill="both", expand=True)

    def _show_purchases(self):
        self._clear_content()
        PurchaseView(self.content, self.user).pack(fill="both", expand=True)

    def _show_reports(self):
        self._clear_content()
        ReportsView(self.content, self.user).pack(fill="both", expand=True)

    def _show_users(self):
        self._clear_content()
        UserManagementView(self.content, self.user).pack(
            fill="both", expand=True
        )

    def _show_logs(self):
        self._clear_content()
        ActivityLogView(self.content, self.user).pack(fill="both", expand=True)

    # ─────────────────────────────────────────────
    # LOGOUT
    # ─────────────────────────────────────────────

    def _logout(self):
        # ---- Ask for confirmation first ----
        confirm = messagebox.askyesno(
            "Confirm Logout",
            "Are you sure you want to log out?",
            icon="question",
        )
        if not confirm:
            return

        # ---- Proceed with logout ----
        AuthController.logout()
        self.destroy()

        from views.login_view import LoginView
        LoginView().mainloop()