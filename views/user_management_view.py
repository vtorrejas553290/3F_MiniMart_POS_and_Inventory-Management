# ─────────────────────────────────────────────
# USER MANAGEMENT VIEW (admin only, staff accounts)
# ─────────────────────────────────────────────

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from controllers.user_controller import UserController
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
# USER MANAGEMENT VIEW
# ─────────────────────────────────────────────

class UserManagementView(ctk.CTkFrame):

    # ---- Pagination size ----
    PAGE_SIZE = 10

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user

        # ---- Pagination state ----
        self.current_page = 1
        self.total_pages = 1

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

        ctk.CTkLabel(title_box, text="User Management",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="Create and manage staff accounts (Owner only)",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ---- Add user button ----
        ctk.CTkButton(header_frame, text="+ Add Staff",
                      height=38, corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._add_dialog).pack(side="right")

        # ═════════════════════════════════════════
        # LIST CARD
        # ═════════════════════════════════════════

        list_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                 corner_radius=12,
                                 border_width=1,
                                 border_color=BORDER)
        list_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # ═════════════════════════════════════════
        # PAGINATION CONTROLS
        # ═════════════════════════════════════════

        pager = ctk.CTkFrame(list_card, fg_color="transparent")
        pager.pack(fill="x", padx=12, pady=(0, 12))

        self.prev_btn = ctk.CTkButton(
            pager, text="‹ Prev",
            width=90, height=32,
            corner_radius=8,
            font=font_bold(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=lambda: self._change_page(-1),
        )
        self.prev_btn.pack(side="left")

        self.page_label = ctk.CTkLabel(
            pager, text="Page 1 of 1",
            font=font_bold(11),
            text_color=FG_SECONDARY,
        )
        self.page_label.pack(side="left", fill="x", expand=True)

        self.next_btn = ctk.CTkButton(
            pager, text="Next ›",
            width=90, height=32,
            corner_radius=8,
            font=font_bold(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=lambda: self._change_page(+1),
        )
        self.next_btn.pack(side="right")

    # ─────────────────────────────────────────────
    # PAGINATION
    # ─────────────────────────────────────────────

    def _change_page(self, delta):
        new_page = self.current_page + delta
        if 1 <= new_page <= self.total_pages:
            self.current_page = new_page
            self._load()

    def _update_pager(self):
        self.page_label.configure(
            text=f"Page {self.current_page} of {self.total_pages}"
        )

        if self.current_page <= 1:
            self.prev_btn.configure(
                state="disabled",
                fg_color=BG_INPUT,
                text_color=FG_MUTED,
            )
        else:
            self.prev_btn.configure(
                state="normal",
                fg_color=NEUTRAL,
                text_color=NEUTRAL_TEXT,
            )

        if self.current_page >= self.total_pages:
            self.next_btn.configure(
                state="disabled",
                fg_color=BG_INPUT,
                text_color=FG_MUTED,
            )
        else:
            self.next_btn.configure(
                state="normal",
                fg_color=NEUTRAL,
                text_color=NEUTRAL_TEXT,
            )

    # ─────────────────────────────────────────────
    # LOAD
    # ─────────────────────────────────────────────

    def _load(self):
        users = UserController.list_users()
        self._render(users)

    # ─────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────

    def _render(self, users):
        for w in self.list_frame.winfo_children():
            w.destroy()

        # ---- Pagination math ----
        total = len(users)
        self.total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages

        start = (self.current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_users = users[start:end]

        # ---- Header ----
        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))

        cols = [
            ("Username",   140),
            ("Full Name",  200),
            ("Role",       100),
            ("Status",     100),
            ("Created",    130),
        ]
        for text, width in cols:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

        # ---- Empty state ----
        if not page_users:
            ctk.CTkLabel(self.list_frame,
                         text="No users yet.",
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            self._update_pager()
            return

        # ---- Rows ----
        for i, u in enumerate(page_users):
            self._render_row(u, i)

        # ---- Update pager ----
        self._update_pager()

    def _render_row(self, u, index):
        bg = BG_ROW_ALT if index % 2 else BG_CARD

        row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=6)
        row.pack(fill="x", pady=2)

        # ---- Username ----
        ctk.CTkLabel(row, text=u["username"],
                     width=140, anchor="w",
                     font=font_bold(12),
                     text_color=FG_PRIMARY).pack(side="left", padx=4, pady=8)

        # ---- Full name (computed from first / middle / last) ----
        ctk.CTkLabel(row, text=u["full_name"],
                     width=200, anchor="w",
                     font=font(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=4)

        # ---- Role ----
        role = u["role"]
        role_color = BRAND_YELLOW if role == "admin" else ACCENT
        ctk.CTkLabel(row, text=role.upper(),
                     width=100, anchor="w",
                     font=font_bold(11),
                     text_color=role_color).pack(side="left", padx=4)

        # ---- Status ----
        is_active = u["is_active"]
        status_text = "Active" if is_active else "Inactive"
        status_color = SUCCESS if is_active else DANGER
        ctk.CTkLabel(row, text=status_text,
                     width=100, anchor="w",
                     font=font_bold(11),
                     text_color=status_color).pack(side="left", padx=4)

        # ---- Created ----
        ctk.CTkLabel(row, text=(u["created_at"] or "")[:10],
                     width=130, anchor="w",
                     font=font(10),
                     text_color=FG_SECONDARY).pack(side="left", padx=4)

        # ---- Actions ----
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=4)

        is_admin = (u["role"] == "admin")

        # ---- Admin accounts: view-only ----
        if is_admin:
            ctk.CTkLabel(actions, text="(owner)",
                         width=80,
                         font=font_bold(10),
                         text_color=FG_MUTED).pack(side="left", padx=2)
            return

        # ---- Staff accounts: Edit + Activate / Deactivate ----
        ctk.CTkButton(actions, text="Edit", width=60, height=30,
                      corner_radius=6,
                      font=font_bold(11),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=lambda usr=u: self._edit_dialog(usr)
                      ).pack(side="left", padx=2)

        if is_active:
            ctk.CTkButton(actions, text="Deactivate", width=90, height=30,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=DANGER, hover_color=DANGER_HOVER,
                          command=lambda usr=u: self._toggle(usr)
                          ).pack(side="left", padx=2)
        else:
            ctk.CTkButton(actions, text="Activate", width=90, height=30,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=BRAND_GREEN, hover_color="#1E9040",
                          command=lambda usr=u: self._toggle(usr)
                          ).pack(side="left", padx=2)

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def _toggle(self, user):
        verb = "deactivate" if user["is_active"] else "activate"
        confirm = messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to {verb} '{user['username']}'?"
        )
        if not confirm:
            return

        ok, msg = UserController.toggle_active(self.user, user["user_id"])
        if ok:
            self._load()
        else:
            messagebox.showerror("Error", msg)

    # ─────────────────────────────────────────────
    # DIALOGS
    # ─────────────────────────────────────────────

    def _add_dialog(self):
        UserDialog(self.winfo_toplevel(), self.user, None,
                   on_save=self._load)

    def _edit_dialog(self, user):
        UserDialog(self.winfo_toplevel(), self.user, user,
                   on_save=self._load)

# ─────────────────────────────────────────────
# USER DIALOG (add / edit staff)
# ─────────────────────────────────────────────

class UserDialog(ctk.CTkToplevel):

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, admin_user, user, on_save):
        super().__init__(parent)
        self.parent = parent
        self.admin_user = admin_user
        self.user = user        # ---- None = adding ----
        self.on_save = on_save

        self.title("Edit Staff" if user else "Add Staff")
        self.geometry("480x620")            # ---- was 500x760 ----
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)

        # ---- Show / hide password state ----
        self.show_pw = False
        self.show_confirm_pw = False

        self._build()
        prepare_dialog_screen(self, self.parent)

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        u = self.user
        is_edit = u is not None

        ctk.CTkLabel(self,
                     text="Edit Staff Account" if is_edit else "Add Staff Account",
                     font=font_bold(16),
                     text_color=FG_PRIMARY).pack(pady=(12, 2))

        ctk.CTkLabel(self,
                     text="Update account details" if is_edit
                          else "Create a login for a staff member",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(pady=(0, 8))

        # ---- Scrollable card (so content never overflows) ----
        card = ctk.CTkScrollableFrame(self, fg_color=BG_CARD,
                                      corner_radius=12,
                                      border_width=1,
                                      border_color=BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # ─────────────────────────────────────
        # USERNAME
        # ─────────────────────────────────────
        ctk.CTkLabel(card, text="USERNAME", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=18, pady=(14, 4))

        self.username_e = ctk.CTkEntry(card, height=34,
                                       corner_radius=8,
                                       font=font(12),
                                       fg_color=BG_INPUT,
                                       border_color=BORDER,
                                       border_width=1)
        self.username_e.pack(fill="x", padx=18)
        if is_edit:
            self.username_e.insert(0, u["username"])
            self.username_e.configure(state="disabled")

        # ─────────────────────────────────────
        # FIRST NAME
        # ─────────────────────────────────────
        ctk.CTkLabel(card, text="FIRST NAME", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=18, pady=(10, 4))

        self.first_e = ctk.CTkEntry(card, height=34,
                                    corner_radius=8,
                                    font=font(12),
                                    fg_color=BG_INPUT,
                                    border_color=BORDER,
                                    border_width=1)
        self.first_e.pack(fill="x", padx=18)
        if is_edit:
            self.first_e.insert(0, u.get("first_name") or "")

        # ─────────────────────────────────────
        # MIDDLE NAME (optional)
        # ─────────────────────────────────────
        ctk.CTkLabel(card, text="MIDDLE NAME (optional)", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=18, pady=(10, 4))

        self.middle_e = ctk.CTkEntry(card, height=34,
                                     corner_radius=8,
                                     font=font(12),
                                     fg_color=BG_INPUT,
                                     border_color=BORDER,
                                     border_width=1)
        self.middle_e.pack(fill="x", padx=18)
        if is_edit:
            self.middle_e.insert(0, u.get("middle_name") or "")

        # ─────────────────────────────────────
        # LAST NAME
        # ─────────────────────────────────────
        ctk.CTkLabel(card, text="LAST NAME", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=18, pady=(10, 4))

        self.last_e = ctk.CTkEntry(card, height=34,
                                   corner_radius=8,
                                   font=font(12),
                                   fg_color=BG_INPUT,
                                   border_color=BORDER,
                                   border_width=1)
        self.last_e.pack(fill="x", padx=18)
        if is_edit:
            self.last_e.insert(0, u.get("last_name") or "")

        # ─────────────────────────────────────
        # ROLE (locked to Staff)
        # ─────────────────────────────────────
        ctk.CTkLabel(card, text="ROLE", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=18, pady=(10, 4))

        role_display = ctk.CTkEntry(card, height=34,
                                    corner_radius=8,
                                    font=font(12),
                                    fg_color=BG_INPUT,
                                    border_color=BORDER,
                                    border_width=1)
        role_display.insert(0, "Staff")
        role_display.configure(state="disabled")
        role_display.pack(fill="x", padx=18)

        # ─────────────────────────────────────
        # PASSWORD
        # ─────────────────────────────────────
        ctk.CTkLabel(card,
                     text="PASSWORD" if not is_edit
                          else "NEW PASSWORD (leave blank to keep)",
                     anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=18, pady=(10, 4))

        pw_row = ctk.CTkFrame(card, height=34, fg_color="transparent")
        pw_row.pack(fill="x", padx=18)
        pw_row.pack_propagate(False)

        self.password_e = ctk.CTkEntry(pw_row, height=34,
                                       corner_radius=8,
                                       font=font(12),
                                       fg_color=BG_INPUT,
                                       border_color=BORDER,
                                       border_width=1,
                                       show="*",
                                       placeholder_text="Minimum 6 characters")
        self.password_e.pack(fill="both", expand=True)

        self.eye_pw = tk.Label(pw_row,
                               text="👁",
                               font=("Segoe UI Emoji", 12),
                               bg="#F8FAFC",
                               fg="#64748B",
                               cursor="hand2",
                               bd=0,
                               highlightthickness=0)
        self.eye_pw.place(relx=0.96, rely=0.5, anchor="e")
        self.eye_pw.bind("<Button-1>", lambda e: self._toggle_pw())

        # ─────────────────────────────────────
        # CONFIRM PASSWORD (only in add mode)
        # ─────────────────────────────────────
        if not is_edit:
            ctk.CTkLabel(card, text="CONFIRM PASSWORD", anchor="w",
                         font=font_bold(10),
                         text_color=FG_SECONDARY).pack(fill="x", padx=18, pady=(10, 4))

            cpw_row = ctk.CTkFrame(card, height=34, fg_color="transparent")
            cpw_row.pack(fill="x", padx=18)
            cpw_row.pack_propagate(False)

            self.confirm_e = ctk.CTkEntry(cpw_row, height=34,
                                          corner_radius=8,
                                          font=font(12),
                                          fg_color=BG_INPUT,
                                          border_color=BORDER,
                                          border_width=1,
                                          show="*",
                                          placeholder_text="Re-enter password")
            self.confirm_e.pack(fill="both", expand=True)

            self.eye_confirm = tk.Label(cpw_row,
                                        text="👁",
                                        font=("Segoe UI Emoji", 12),
                                        bg="#F8FAFC",
                                        fg="#64748B",
                                        cursor="hand2",
                                        bd=0,
                                        highlightthickness=0)
            self.eye_confirm.place(relx=0.96, rely=0.5, anchor="e")
            self.eye_confirm.bind("<Button-1>",
                                  lambda e: self._toggle_confirm_pw())
        else:
            self.confirm_e = None

        # ─────────────────────────────────────
        # SAVE
        # ─────────────────────────────────────
        ctk.CTkButton(card,
                      text="Save" if not is_edit else "Save Changes",
                      width=200, height=38,
                      corner_radius=8,
                      font=font_bold(13),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._save).pack(pady=(14, 14))

    # ─────────────────────────────────────────────
    # PASSWORD TOGGLES
    # ─────────────────────────────────────────────

    def _toggle_pw(self):
        if self.show_pw:
            self.password_e.configure(show="*")
            self.eye_pw.configure(text="👁")
            self.show_pw = False
        else:
            self.password_e.configure(show="")
            self.eye_pw.configure(text="🙈")
            self.show_pw = True

    def _toggle_confirm_pw(self):
        if self.show_confirm_pw:
            self.confirm_e.configure(show="*")
            self.eye_confirm.configure(text="👁")
            self.show_confirm_pw = False
        else:
            self.confirm_e.configure(show="")
            self.eye_confirm.configure(text="🙈")
            self.show_confirm_pw = True

    # ─────────────────────────────────────────────
    # SAVE
    # ─────────────────────────────────────────────

    def _save(self):
        username = self.username_e.get().strip().lower()
        first_name = self.first_e.get().strip()
        middle_name = self.middle_e.get().strip()
        last_name = self.last_e.get().strip()
        password = self.password_e.get().strip()

        # ═════════════════════════════════════════
        # ADD MODE
        # ═════════════════════════════════════════
        if self.user is None:
            confirm = self.confirm_e.get().strip() if self.confirm_e else ""

            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match.")
                return

            ok, msg = UserController.add_user(
                self.admin_user, username, password,
                first_name, middle_name, last_name,
            )
            if ok:
                messagebox.showinfo("Staff Created",
                                    f"Account for '{username}' created.")
                self.on_save()
                self.destroy()
            else:
                messagebox.showerror("Error", msg)
            return

        # ═════════════════════════════════════════
        # EDIT MODE
        # ═════════════════════════════════════════
        new_password = password if password else None
        ok, msg = UserController.edit_user(
            self.admin_user,
            self.user["user_id"],
            first_name, middle_name, last_name,
            new_password,
        )
        if ok:
            messagebox.showinfo("Staff Updated",
                                f"Account for '{self.user['username']}' updated.")
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)