# ─────────────────────────────────────────────
# SUPPLIER VIEW
# ─────────────────────────────────────────────

import customtkinter as ctk
from tkinter import messagebox

from controllers.supplier_controller import SupplierController
from utils import prepare_dialog_screen
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BG_INPUT, BG_ROW_ALT, BORDER,
    FG_PRIMARY, FG_SECONDARY, FG_MUTED,
    BRAND_GREEN, BRAND_YELLOW,
    ACCENT, ACCENT_HOVER, SUCCESS, DANGER, DANGER_HOVER,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


class SupplierView(ctk.CTkFrame):

    PAGE_SIZE = 10

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user
        self.show_archived = False
        self.supplier_categories = SupplierController.list_supplier_categories()
        self.selected_category_id = None
        self.search_query = ""

        self.current_page = 1
        self.total_pages = 1

        self._build()
        self._load()

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        # ---- Header ----
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box, text="Suppliers",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="Manage your suppliers and their contact information",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        actions = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions.pack(side="right")

        ctk.CTkButton(actions, text="+ Add Supplier",
                      height=38, corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._add_dialog).pack(side="right", padx=(6, 0))

        ctk.CTkButton(actions, text="+ Add Supplier Category",
                      height=38, corner_radius=8,
                      font=font_bold(12),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._add_category_dialog).pack(side="right", padx=(6, 0))

        # ---- Filter card ----
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
            placeholder_text="Search by name, category, contact no., contact person, address...",
            textvariable=self.search_var,
            width=320, height=36, corner_radius=8, font=font(12),
            fg_color=BG_INPUT, border_color=BORDER, border_width=1,
        )
        self.search_e.pack(side="left", padx=(0, 8))

        ctk.CTkButton(row1, text="✕", width=36, height=36,
                      corner_radius=8, font=font(13),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._clear_search).pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row1, text="Category",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.category_names = ["All Categories"] + [
            c["name"] for c in self.supplier_categories
        ]
        self.category_var = ctk.StringVar(value="All Categories")

        self.category_menu = ctk.CTkOptionMenu(
            row1, values=self.category_names, variable=self.category_var,
            width=180, height=36, corner_radius=8, font=font(12),
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=NEUTRAL, text_color=FG_PRIMARY,
            command=self._on_category_change,
        )
        self.category_menu.pack(side="left", padx=(0, 20))

        self.archive_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(row1, text="Show Archived",
                        variable=self.archive_var,
                        font=font(12),
                        command=self._toggle_archived).pack(side="left")

        row2 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 14))

        self.count_label = ctk.CTkLabel(row2, text="",
                                        font=font_bold(11),
                                        text_color=FG_SECONDARY)
        self.count_label.pack(side="right", padx=(0, 4))

        # ---- List card ----
        list_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                 corner_radius=12, border_width=1,
                                 border_color=BORDER)
        list_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        pager = ctk.CTkFrame(list_card, fg_color="transparent")
        pager.pack(fill="x", padx=12, pady=(0, 12))

        self.prev_btn = ctk.CTkButton(
            pager, text="‹ Prev", width=90, height=32,
            corner_radius=8, font=font_bold(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=lambda: self._change_page(-1),
        )
        self.prev_btn.pack(side="left")

        self.page_label = ctk.CTkLabel(pager, text="Page 1 of 1",
                                       font=font_bold(11),
                                       text_color=FG_SECONDARY)
        self.page_label.pack(side="left", fill="x", expand=True)

        self.next_btn = ctk.CTkButton(
            pager, text="Next ›", width=90, height=32,
            corner_radius=8, font=font_bold(11),
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
            self.prev_btn.configure(state="disabled",
                                    fg_color=BG_INPUT, text_color=FG_MUTED)
        else:
            self.prev_btn.configure(state="normal",
                                    fg_color=NEUTRAL, text_color=NEUTRAL_TEXT)

        if self.current_page >= self.total_pages:
            self.next_btn.configure(state="disabled",
                                    fg_color=BG_INPUT, text_color=FG_MUTED)
        else:
            self.next_btn.configure(state="normal",
                                    fg_color=NEUTRAL, text_color=NEUTRAL_TEXT)

    # ─────────────────────────────────────────────
    # FILTERS
    # ─────────────────────────────────────────────

    def _on_search_change(self, *args):
        self.search_query = self.search_var.get().strip().lower()
        self.current_page = 1
        self._load()

    def _clear_search(self):
        self.search_var.set("")

    def _on_category_change(self, choice):
        if choice == "All Categories":
            self.selected_category_id = None
        else:
            self.selected_category_id = None
            for c in self.supplier_categories:
                if c["name"] == choice:
                    self.selected_category_id = c["scat_id"]
                    break
        self.current_page = 1
        self._load()

    def _toggle_archived(self):
        self.show_archived = self.archive_var.get()
        self.current_page = 1
        self._load()

    # ─────────────────────────────────────────────
    # LOAD
    # ─────────────────────────────────────────────

    def _load(self):
        suppliers = SupplierController.list_suppliers(
            include_archived=self.show_archived
        )

        if self.selected_category_id is not None:
            suppliers = [
                s for s in suppliers
                if s["supplier_category_id"] == self.selected_category_id
            ]

        if self.search_query:
            suppliers = [s for s in suppliers if self._matches_search(s)]

        self._render(suppliers)

    def _matches_search(self, s):
        q = self.search_query
        fields = [
            (s["name"] or "").lower(),
            (s["supplier_category_name"] or "").lower(),
            (s["contact_number"] or "").lower(),
            (s["contact_person"] or "").lower(),
            (s["address"] or "").lower(),
        ]
        return any(q in f for f in fields)

    # ─────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────

    def _render(self, suppliers):
        for w in self.list_frame.winfo_children():
            w.destroy()

        total = len(suppliers)
        self.count_label.configure(text=f"{total} supplier(s)")

        self.total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages

        start = (self.current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_suppliers = suppliers[start:end]

        # ---- Header ----
        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))
        cols = [
            ("Name",             180),
            ("Supplier Category", 140),
            ("Contact Person",    160),
            ("Contact No.",       130),
            ("Address",           180),
        ]
        for text, width in cols:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

        if not page_suppliers:
            msg = "No suppliers match your search." if self.search_query \
                  else "No suppliers to show."
            ctk.CTkLabel(self.list_frame, text=msg,
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            self._update_pager()
            return

        for i, s in enumerate(page_suppliers):
            self._render_row(s, i)

        self._update_pager()

    def _render_row(self, s, index=0):
        bg = BG_ROW_ALT if index % 2 else BG_CARD

        row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=6)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=s["name"], width=180,
                     anchor="w",
                     font=font_bold(12),
                     text_color=FG_PRIMARY).pack(side="left", padx=4, pady=8)

        ctk.CTkLabel(row, text=s["supplier_category_name"] or "-",
                     width=140, anchor="w",
                     font=font(11),
                     text_color=ACCENT).pack(side="left", padx=4)

        ctk.CTkLabel(row, text=s["contact_person"] or "-",
                     width=160, anchor="w",
                     font=font(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=4)

        ctk.CTkLabel(row, text=s["contact_number"] or "-",
                     width=130, anchor="w",
                     font=font(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=4)

        ctk.CTkLabel(row, text=s["address"] or "-",
                     width=180, anchor="w",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=4)

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=4)

        if s["is_archived"]:
            ctk.CTkButton(actions, text="Restore", width=70, height=30,
                          corner_radius=6, font=font_bold(11),
                          fg_color=BRAND_GREEN, hover_color="#1E9040",
                          command=lambda sup=s: self._restore(sup)
                          ).pack(side="left", padx=2)
        else:
            ctk.CTkButton(actions, text="Edit", width=60, height=30,
                          corner_radius=6, font=font_bold(11),
                          fg_color=ACCENT, hover_color=ACCENT_HOVER,
                          command=lambda sup=s: self._edit_dialog(sup)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="Archive", width=70, height=30,
                          corner_radius=6, font=font_bold(11),
                          fg_color=DANGER, hover_color=DANGER_HOVER,
                          command=lambda sup=s: self._archive(sup)
                          ).pack(side="left", padx=2)

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def _archive(self, supplier):
        if not messagebox.askyesno(
            "Archive Supplier",
            f"Archive '{supplier['name']}'?\n\n"
            "Archived suppliers are hidden but kept in history."
        ):
            return

        ok, msg = SupplierController.archive(
            self.user, supplier["supplier_id"], supplier["name"]
        )
        if ok:
            messagebox.showinfo("Archived", f"'{supplier['name']}' archived.")
            self._load()
        else:
            messagebox.showerror("Error", msg)

    def _restore(self, supplier):
        ok, msg = SupplierController.unarchive(
            self.user, supplier["supplier_id"], supplier["name"]
        )
        if ok:
            self._load()
        else:
            messagebox.showerror("Error", msg)

    # ─────────────────────────────────────────────
    # DIALOGS
    # ─────────────────────────────────────────────

    def _add_dialog(self):
        SupplierDialog(self.winfo_toplevel(), self.user, None,
                       on_save=self._after_supplier_saved)

    def _edit_dialog(self, supplier):
        SupplierDialog(self.winfo_toplevel(), self.user, supplier,
                       on_save=self._after_supplier_saved)

    def _add_category_dialog(self):
        SupplierCategoryDialog(self.winfo_toplevel(), self.user,
                               on_save=self._refresh_categories)

    def _after_supplier_saved(self):
        self._load()

    def _refresh_categories(self):
        self.supplier_categories = SupplierController.list_supplier_categories()
        self.category_names = ["All Categories"] + [
            c["name"] for c in self.supplier_categories
        ]
        self.category_menu.configure(values=self.category_names)
        self._load()


# ─────────────────────────────────────────────
# SUPPLIER DIALOG
# ─────────────────────────────────────────────

class SupplierDialog(ctk.CTkToplevel):

    def __init__(self, parent, user, supplier, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.supplier = supplier
        self.on_save = on_save
        self.title("Supplier")
        self.geometry("500x600")
        self.resizable(True, True)
        self.minsize(480, 500)
        self.configure(fg_color=BG_MAIN)

        self.supplier_categories = SupplierController.list_supplier_categories()

        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        s = self.supplier
        is_edit = s is not None

        # ---- Header ----
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(header,
                     text="Edit Supplier" if is_edit else "New Supplier",
                     font=font_bold(15),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(side="left")

        ctk.CTkButton(header, text="✕", width=30, height=30,
                      corner_radius=6, font=font_bold(13),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self.destroy).pack(side="right")

        # ---- Scrollable card ----
        card = ctk.CTkScrollableFrame(self, fg_color=BG_CARD,
                                      corner_radius=10, border_width=1,
                                      border_color=BORDER)
        card.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        # ---- Name (required) ----
        self._label(card, "NAME  *")
        self.name_e = self._entry(card)
        if s: self.name_e.insert(0, s["name"])

        # ---- Category ----
        self._label(card, "SUPPLIER CATEGORY  *")

        cat_row = ctk.CTkFrame(card, fg_color="transparent")
        cat_row.pack(fill="x", padx=12)

        cat_names = [c["name"] for c in self.supplier_categories] or ["(No categories)"]
        self.category_var = ctk.StringVar(
            value=s["supplier_category_name"] if s and s["supplier_category_name"]
            else cat_names[0]
        )
        self.category_menu = ctk.CTkOptionMenu(
            cat_row, values=cat_names, variable=self.category_var,
            height=32, corner_radius=6, font=font(12),
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=NEUTRAL, text_color=FG_PRIMARY,
        )
        self.category_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(cat_row, text="+", width=32, height=32,
                      corner_radius=6, font=font_bold(13),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._quick_add_category).pack(side="left")

        # ---- Contact Person (first required) ----
        self._label(card, "CONTACT PERSON  (first name required)")

        cp_row = ctk.CTkFrame(card, fg_color="transparent")
        cp_row.pack(fill="x", padx=12)

        first_col = ctk.CTkFrame(cp_row, fg_color="transparent")
        first_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(first_col, text="First name  *", anchor="w",
                     font=font_bold(9), text_color=FG_SECONDARY).pack(fill="x", pady=(0, 2))
        self.cp_first_e = ctk.CTkEntry(first_col, height=30, corner_radius=6,
                                       font=font(12), fg_color=BG_INPUT,
                                       border_color=BORDER, border_width=1)
        self.cp_first_e.pack(fill="x")
        if s and s.get("contact_person_first"):
            self.cp_first_e.insert(0, s["contact_person_first"])

        mid_col = ctk.CTkFrame(cp_row, fg_color="transparent")
        mid_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(mid_col, text="Middle (optional)", anchor="w",
                     font=font_bold(9), text_color=FG_SECONDARY).pack(fill="x", pady=(0, 2))
        self.cp_mid_e = ctk.CTkEntry(mid_col, height=30, corner_radius=6,
                                     font=font(12), fg_color=BG_INPUT,
                                     border_color=BORDER, border_width=1)
        self.cp_mid_e.pack(fill="x")
        if s and s.get("contact_person_middle"):
            self.cp_mid_e.insert(0, s["contact_person_middle"])

        last_col = ctk.CTkFrame(cp_row, fg_color="transparent")
        last_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(last_col, text="Last (optional)", anchor="w",
                     font=font_bold(9), text_color=FG_SECONDARY).pack(fill="x", pady=(0, 2))
        self.cp_last_e = ctk.CTkEntry(last_col, height=30, corner_radius=6,
                                      font=font(12), fg_color=BG_INPUT,
                                      border_color=BORDER, border_width=1)
        self.cp_last_e.pack(fill="x")
        if s and s.get("contact_person_last"):
            self.cp_last_e.insert(0, s["contact_person_last"])

        # ---- Contact Number (required) ----
        self._label(card, "CONTACT NUMBER  *")
        self.contact_e = self._entry(card)
        if s: self.contact_e.insert(0, s["contact_number"] or "")

        # ---- Address ----
        self._label(card, "ADDRESS")
        self.address_e = self._entry(card)
        if s and s["address"]: self.address_e.insert(0, s["address"])

        # ---- Save ----
        ctk.CTkButton(card, text="Save Supplier",
                      height=38, corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._save).pack(fill="x", padx=12, pady=(14, 12))

    # ---- Layout helpers ----
    def _label(self, parent, text):
        ctk.CTkLabel(parent, text=text, anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(8, 3))

    def _entry(self, parent):
        e = ctk.CTkEntry(parent, height=30, corner_radius=6, font=font(12),
                         fg_color=BG_INPUT, border_color=BORDER, border_width=1)
        e.pack(fill="x", padx=12)
        return e

    # ─────────────────────────────────────────────
    # QUICK ADD CATEGORY
    # ─────────────────────────────────────────────

    def _quick_add_category(self):
        prompt = ctk.CTkToplevel(self)
        prompt.title("Quick Add Supplier Category")
        prompt.geometry("340x220")
        prompt.resizable(False, False)
        prompt.configure(fg_color=BG_MAIN)

        ctk.CTkLabel(prompt, text="New Supplier Category",
                     font=font_bold(13),
                     text_color=FG_PRIMARY).pack(pady=(16, 4))

        name_e = ctk.CTkEntry(prompt, width=240, height=34,
                              corner_radius=6, font=font(12),
                              fg_color=BG_INPUT, border_color=BORDER,
                              border_width=1, placeholder_text="Category name")
        name_e.pack(pady=(8, 16))
        name_e.focus_set()

        def save():
            name = name_e.get().strip()
            if not name:
                messagebox.showerror("Error", "Category name is required.")
                return
            ok, msg = SupplierController.add_supplier_category(self.user, name)
            if not ok:
                messagebox.showerror("Error", msg)
                return
            self.supplier_categories = SupplierController.list_supplier_categories()
            self.category_menu.configure(
                values=[c["name"] for c in self.supplier_categories]
            )
            self.category_var.set(name)
            prompt.destroy()

        ctk.CTkButton(prompt, text="Save", width=240, height=36,
                      corner_radius=8, font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=save).pack(pady=(0, 20))
        prepare_dialog_screen(prompt, self)

    # ─────────────────────────────────────────────
    # SAVE
    # ─────────────────────────────────────────────

    def _save(self):
        name = self.name_e.get().strip()
        contact_number = self.contact_e.get().strip()
        cp_first = self.cp_first_e.get().strip()
        cp_mid = self.cp_mid_e.get().strip() or None
        cp_last = self.cp_last_e.get().strip() or None
        address = self.address_e.get().strip() or None

        if not name:
            messagebox.showerror("Error", "Supplier name is required.")
            return
        if not contact_number:
            messagebox.showerror("Error", "Contact number is required.")
            return
        if not cp_first:
            messagebox.showerror("Error", "Contact person's first name is required.")
            return

        scat_id = None
        for c in self.supplier_categories:
            if c["name"] == self.category_var.get():
                scat_id = c["scat_id"]
                break

        if scat_id is None:
            messagebox.showerror("Error", "Please select a supplier category.")
            return

        if self.supplier:
            ok, msg = SupplierController.update(
                self.user, self.supplier["supplier_id"],
                name, contact_number, scat_id,
                cp_first, cp_mid, cp_last, address,
            )
        else:
            ok, msg = SupplierController.add(
                self.user, name, contact_number, scat_id,
                cp_first, cp_mid, cp_last, address,
            )

        if ok:
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


# ─────────────────────────────────────────────
# SUPPLIER CATEGORY DIALOG
# ─────────────────────────────────────────────

class SupplierCategoryDialog(ctk.CTkToplevel):

    def __init__(self, parent, user, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.on_save = on_save
        self.title("Manage Supplier Categories")
        self.geometry("500x480")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        ctk.CTkLabel(self, text="Manage Supplier Categories",
                     font=font_bold(15),
                     text_color=FG_PRIMARY).pack(pady=(14, 4))

        card = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=10, border_width=1,
                            border_color=BORDER)
        card.pack(fill="both", expand=True, padx=14, pady=(6, 14))

        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=12, pady=(12, 4))

        self.name_e = ctk.CTkEntry(add_row, height=34,
                                   placeholder_text="New category name",
                                   corner_radius=6, font=font(12),
                                   fg_color=BG_INPUT, border_color=BORDER,
                                   border_width=1)
        self.name_e.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(add_row, text="Add", width=60, height=34,
                      corner_radius=6, font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._add).pack(side="left")

        self.desc_e = ctk.CTkEntry(card, height=34,
                                   placeholder_text="Description (optional)",
                                   corner_radius=6, font=font(12),
                                   fg_color=BG_INPUT, border_color=BORDER,
                                   border_width=1)
        self.desc_e.pack(fill="x", padx=12, pady=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self._load_categories()

    def _load_categories(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        cats = SupplierController.list_supplier_categories()
        if not cats:
            ctk.CTkLabel(self.list_frame,
                         text="No supplier categories yet.",
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=20)
            return

        for i, c in enumerate(cats):
            bg = BG_ROW_ALT if i % 2 else BG_CARD
            row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=c["name"], anchor="w",
                         font=font_bold(12),
                         text_color=FG_PRIMARY).pack(side="left", padx=10, pady=8)

            ctk.CTkLabel(row, text=c["description"] or "", anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=(6, 10))

    def _add(self):
        name = self.name_e.get().strip()
        desc = self.desc_e.get().strip()

        if not name:
            messagebox.showerror("Error", "Category name is required.")
            return

        ok, msg = SupplierController.add_supplier_category(self.user, name, desc)
        if not ok:
            messagebox.showerror("Error", msg)
            return

        self.name_e.delete(0, "end")
        self.desc_e.delete(0, "end")
        self._load_categories()
        self.on_save()