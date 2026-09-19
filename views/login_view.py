# ─────────────────────────────────────────────
# LOGIN VIEW (softened 3F MiniMart branding)
# ─────────────────────────────────────────────

import tkinter as tk
import customtkinter as ctk
from controllers.auth_controller import AuthController
from config import (
    APP_NAME, font, font_bold,
    BRAND_GREEN, BRAND_BLUE, BRAND_YELLOW,
    BG_MAIN, BG_CARD, BG_INPUT,
    FG_PRIMARY, FG_SECONDARY, FG_ON_BRAND,
    ACCENT, ACCENT_HOVER, DANGER, BORDER,
)
from utils import maximize


class LoginView(ctk.CTk):

    # ---- Setup ----

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Login")
        self.configure(fg_color=BG_MAIN)

        self.after(0, lambda: maximize(self))
        self.minsize(900, 600)

        self._build()

    # ---- Build ----

    def _build(self):
        # ═════════════════════════════════════════
        # LEFT PANEL — DEEP NAVY brand wall
        # ═════════════════════════════════════════

        left = ctk.CTkFrame(self, width=520, corner_radius=0,
                            fg_color="#1E3A8A")
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        brand = ctk.CTkFrame(left, fg_color="transparent")
        brand.place(relx=0.5, rely=0.42, anchor="center")

        # ---- "3F" in soft green ----
        ctk.CTkLabel(brand, text="3F",
                     font=font_bold(84),
                     text_color=BRAND_GREEN).pack()

        # ---- "MiniMart" in white ----
        ctk.CTkLabel(brand, text="MiniMart",
                     font=font_bold(30),
                     text_color="#FFFFFF").pack(pady=(0, 14))

        # ---- Yellow pill under logo (auto-sizing) ----
        pill = ctk.CTkFrame(brand, fg_color=BRAND_YELLOW,
                            corner_radius=16)
        pill.pack(pady=(0, 20))

        ctk.CTkLabel(
            pill,
            text="Point-of-Sale & Inventory System",
            font=font_bold(11),
            text_color="#0F172A",
            padx=18,
            pady=8,
        ).pack()

        # ---- Footer ----
        ctk.CTkLabel(left,
                     text="© 2026 3F MiniMart",
                     font=font(10),
                     text_color="#94A3B8").pack(side="bottom", pady=20)

        # ═════════════════════════════════════════
        # RIGHT PANEL — clean white login
        # ═════════════════════════════════════════

        right = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_MAIN)
        right.pack(side="right", fill="both", expand=True)

        form = ctk.CTkFrame(right, fg_color="transparent")
        form.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(form, text="Welcome back",
                     font=font_bold(24),
                     text_color=FG_PRIMARY).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(form, text="Sign in to continue to your dashboard",
                     font=font(12),
                     text_color=FG_SECONDARY).pack(anchor="w", pady=(0, 30))

        # ---- Username ----
        ctk.CTkLabel(form, text="USERNAME", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", pady=(0, 6))

        self.username_entry = ctk.CTkEntry(
            form,
            placeholder_text="Enter your username",
            width=360, height=42,
            corner_radius=8,
            font=font(13),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
        )
        self.username_entry.pack(pady=(0, 18))

        # ---- Password ----
        ctk.CTkLabel(form, text="PASSWORD", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", pady=(0, 6))

        pw_container = ctk.CTkFrame(form, width=360, height=42,
                                    fg_color="transparent")
        pw_container.pack()
        pw_container.pack_propagate(False)

        self.password_entry = ctk.CTkEntry(
            pw_container,
            placeholder_text="Enter your password",
            show="*",
            height=42,
            corner_radius=8,
            font=font(13),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
        )
        self.password_entry.pack(fill="both", expand=True)

        # ---- Eye toggle ----
        self.show_pw = False
        self.eye_label = tk.Label(
            pw_container,
            text="👁",
            font=("Segoe UI Emoji", 12),
            bg="#F8FAFC",
            fg="#64748B",
            cursor="hand2",
            bd=0,
            highlightthickness=0,
        )
        self.eye_label.place(relx=0.96, rely=0.5, anchor="e")
        self.eye_label.bind("<Button-1>", lambda e: self._toggle_password())

        # ---- Message ----
        self.msg_label = ctk.CTkLabel(form, text="",
                                      text_color=DANGER,
                                      font=font(11))
        self.msg_label.pack(pady=(14, 0))

        # ---- Login button (soft blue) ----
        ctk.CTkButton(
            form,
            text="Sign In",
            width=360, height=44,
            corner_radius=8,
            font=font_bold(14),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._on_login,
        ).pack(pady=(16, 12))

        # ---- Focus + Enter ----
        self.username_entry.focus_set()
        self.bind("<Return>", lambda e: self._on_login())

    # ---- Password toggle ----

    def _toggle_password(self):
        if self.show_pw:
            self.password_entry.configure(show="*")
            self.eye_label.configure(text="👁")
            self.show_pw = False
        else:
            self.password_entry.configure(show="")
            self.eye_label.configure(text="🙈")
            self.show_pw = True

    # ---- Events ----

    def _on_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.msg_label.configure(text="Please fill in all fields.")
            return

        ok, msg = AuthController.login(username, password)
        if ok:
            self.destroy()
            from views.main_window import MainWindow
            MainWindow().mainloop()
        else:
            self.msg_label.configure(text=msg)