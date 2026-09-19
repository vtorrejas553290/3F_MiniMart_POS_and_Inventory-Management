# ─────────────────────────────────────────────
# SUPPLIER VIEW (softened 3F MiniMart branding)
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


# ─────────────────────────────────────────────
# SUPPLIER VIEW
# ─────────────────────────────────────────────

class SupplierView(ctk.CTkFrame):

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user
        self.show_archived = False
        self.supplier_categories = SupplierController.list_supplier_categories()
        self.selected_category_id = None
        self.search_query = ""
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

        ctk.CTkLabel(title_box, text="Suppliers",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="Manage your suppliers and their contact information",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ---- Primary actions ----
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

        # ═════════════════════════════════════════
        # FILTER CARD
        # ═════════════════════════════════════════

        filter_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                   corner_radius=12,
                                   border_width=1,
                                   border_color=BORDER)
        filter_card.pack(fill="x", padx=20, pady=(0, 10))

        # ---- Row 1: search + category ----
        row1 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(14, 6))

        # ---- Search ----
        ctk.CTkLabel(row1, text="Search",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        self.search_e = ctk.CTkEntry(
            row1,
            placeholder_text="Search by name, category, contact, address...",
            textvariable=self.search_var,
            width=320, height=36,
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

        # ---- Supplier Category filter ----
        ctk.CTkLabel(row1, text="Category",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.category_names = ["All Categories"] + [
            c["name"] for c in self.supplier_categories
        ]
        self.category_var = ctk.StringVar(value="All Categories")

        self.category_menu = ctk.CTkOptionMenu(
            row1,
            values=self.category_names,
            variable=self.category_var,
            width=180, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=NEUTRAL,
            text_color=FG_PRIMARY,
            command=self._on_category_change,
        )
        self.category_menu.pack(side="left", padx=(0, 20))

        # ---- Archive toggle ----
        self.archive_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(row1, text="Show Archived",
                        variable=self.archive_var,
                        font=font(12),
                        command=self._toggle_archived).pack(side="left")

        # ---- Row 2: count ----
        row2 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 14))

        self.count_label = ctk.CTkLabel(row2, text="",
                                        font=font_bold(11),
                                        text_color=FG_SECONDARY)
        self.count_label.pack(side="right", padx=(0, 4))

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

    # ─────────────────────────────────────────────
    # SEARCH
    # ─────────────────────────────────────────────

    def _on_search_change(self, *args):
        self.search_query = self.search_var.get().strip().lower()
        self._load()

    def _clear_search(self):
        self.search_var.set("")

    # ─────────────────────────────────────────────
    # FILTER + TOGGLE
    # ─────────────────────────────────────────────

    def _on_category_change(self, choice):
        if choice == "All Categories":
            self.selected_category_id = None
        else:
            self.selected_category_id = None
            for c in self.supplier_categories:
                if c["name"] == choice:
                    self.selected_category_id = c["scat_id"]
                    break
        self._load()

    def _toggle_archived(self):
        self.show_archived = self.archive_var.get()
        self._load()

    # ─────────────────────────────────────────────
    # LOAD
    # ─────────────────────────────────────────────

    def _load(self):
        suppliers = SupplierController.list_suppliers()

        if not self.show_archived:
            suppliers = [s for s in suppliers if s["is_archived"] == 0]

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
            (s["contact"] or "").lower(),
            (s["address"] or "").lower(),
        ]
        return any(q in f for f in fields)

    # ─────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────

    def _render(self, suppliers):
        for w in self.list_frame.winfo_children():
            w.destroy()

        self.count_label.configure(text=f"{len(suppliers)} supplier(s)")

        # ---- Header ----
        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))
        cols = [
            ("Name",                 200),
            ("Supplier Category",    170),
            ("Contact",              160),
            ("Address",              220),
        ]
        for text, width in cols:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

        # ---- Empty state ----
        if not suppliers:
            msg = "No suppliers match your search." if self.search_query \
                  else "No suppliers to show."
            ctk.CTkLabel(self.list_frame, text=msg,
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            return

        # ---- Rows ----
        for i, s in enumerate(suppliers):
            self._render_row(s, i)

    def _render_row(self, s, index=0):
        # ---- Zebra striping ----
        bg = BG_ROW_ALT if index % 2 else BG_CARD

        row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=6)
        row.pack(fill="x", pady=2)

        # ---- Name ----
        ctk.CTkLabel(row, text=s["name"], width=200,
                     anchor="w",
                     font=font_bold(12),
                     text_color=FG_PRIMARY).pack(side="left", padx=4, pady=8)

        # ---- Supplier Category ----
        ctk.CTkLabel(row, text=s["supplier_category_name"] or "-",
                     width=170, anchor="w",
                     font=font(11),
                     text_color=ACCENT).pack(side="left", padx=4)

        # ---- Contact ----
        ctk.CTkLabel(row, text=s["contact"] or "-",
                     width=160, anchor="w",
                     font=font(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=4)

        # ---- Address ----
        ctk.CTkLabel(row, text=s["address"] or "-",
                     width=220, anchor="w",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=4)

        # ---- Actions ----
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=4)

        if s["is_archived"]:
            ctk.CTkButton(actions, text="Restore", width=70, height=30,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=BRAND_GREEN, hover_color="#1E9040",
                          command=lambda sup=s: self._restore(sup)
                          ).pack(side="left", padx=2)
        else:
            ctk.CTkButton(actions, text="Edit", width=60, height=30,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=ACCENT, hover_color=ACCENT_HOVER,
                          command=lambda sup=s: self._edit_dialog(sup)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="Archive", width=70, height=30,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=DANGER, hover_color=DANGER_HOVER,
                          command=lambda sup=s: self._archive(sup)
                          ).pack(side="left", padx=2)

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def _archive(self, supplier):
        confirm = messagebox.askyesno(
            "Archive Supplier",
            f"Archive '{supplier['name']}'?\n\n"
            "Archived suppliers are hidden but kept in history."
        )
        if not confirm:
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

    # ─────────────────────────────────────────────
    # REFRESH HELPERS
    # ─────────────────────────────────────────────

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
# SUPPLIER DIALOG (add / edit) — styled
# ─────────────────────────────────────────────

class SupplierDialog(ctk.CTkToplevel):

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user, supplier, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.supplier = supplier
        self.on_save = on_save
        self.title("Supplier")
        self.geometry("480x480")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)

        self.supplier_categories = SupplierController.list_supplier_categories()

        self._build()
        prepare_dialog_screen(self, self.parent)

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        s = self.supplier

        # ---- Title ----
        ctk.CTkLabel(self,
                     text="Edit Supplier" if s else "New Supplier",
                     font=font_bold(16),
                     text_color=FG_PRIMARY).pack(pady=(16, 4))

        # ---- Card ----
        card = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        # ---- Name ----
        ctk.CTkLabel(card, text="NAME", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=20, pady=(18, 4))
        self.name_e = ctk.CTkEntry(card, height=36,
                                   corner_radius=8,
                                   font=font(12),
                                   fg_color=BG_INPUT,
                                   border_color=BORDER,
                                   border_width=1)
        self.name_e.pack(fill="x", padx=20)
        if s: self.name_e.insert(0, s["name"])

        # ---- Contact ----
        ctk.CTkLabel(card, text="CONTACT", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=20, pady=(12, 4))
        self.contact_e = ctk.CTkEntry(card, height=36,
                                      corner_radius=8,
                                      font=font(12),
                                      fg_color=BG_INPUT,
                                      border_color=BORDER,
                                      border_width=1)
        self.contact_e.pack(fill="x", padx=20)
        if s: self.contact_e.insert(0, s["contact"] or "")

        # ---- Address ----
        ctk.CTkLabel(card, text="ADDRESS", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=20, pady=(12, 4))
        self.address_e = ctk.CTkEntry(card, height=36,
                                      corner_radius=8,
                                      font=font(12),
                                      fg_color=BG_INPUT,
                                      border_color=BORDER,
                                      border_width=1)
        self.address_e.pack(fill="x", padx=20)
        if s: self.address_e.insert(0, s["address"] or "")

        # ---- Supplier Category ----
        ctk.CTkLabel(card, text="SUPPLIER CATEGORY", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=20, pady=(12, 4))

        cat_row = ctk.CTkFrame(card, fg_color="transparent")
        cat_row.pack(fill="x", padx=20)

        cat_names = [c["name"] for c in self.supplier_categories] or ["(No categories)"]
        self.category_var = ctk.StringVar(
            value=s["supplier_category_name"] if s and s["supplier_category_name"]
            else cat_names[0]
        )
        self.category_menu = ctk.CTkOptionMenu(
            cat_row, values=cat_names, variable=self.category_var,
            height=36, corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=NEUTRAL,
            text_color=FG_PRIMARY,
        )
        self.category_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(cat_row, text="+", width=36, height=36,
                      corner_radius=8,
                      font=font_bold(14),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._quick_add_category).pack(side="left")

        # ---- Save ----
        ctk.CTkButton(card, text="Save Supplier",
                      width=200, height=40,
                      corner_radius=8,
                      font=font_bold(13),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._save).pack(pady=(20, 18))

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
                     font=font_bold(14),
                     text_color=FG_PRIMARY).pack(pady=(20, 4))

        name_e = ctk.CTkEntry(prompt, width=240, height=36,
                              corner_radius=8,
                              font=font(12),
                              fg_color=BG_INPUT,
                              border_color=BORDER,
                              border_width=1,
                              placeholder_text="Category name")
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

        ctk.CTkButton(prompt, text="Save", width=240, height=38,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=save).pack(pady=(0, 20))
        prepare_dialog_screen(prompt, self)

    # ─────────────────────────────────────────────
    # SAVE
    # ─────────────────────────────────────────────

    def _save(self):
        name = self.name_e.get().strip()
        contact = self.contact_e.get().strip()
        address = self.address_e.get().strip()

        if not name:
            messagebox.showerror("Error", "Supplier name is required.")
            return

        scat_id = None
        for c in self.supplier_categories:
            if c["name"] == self.category_var.get():
                scat_id = c["scat_id"]
                break

        if scat_id is None:
            messagebox.showerror("Error",
                                 "Please select a supplier category. "
                                 "Every supplier must belong to one category.")
            return

        if self.supplier:
            ok, msg = SupplierController.update(
                self.user, self.supplier["supplier_id"],
                name, contact, address, scat_id
            )
        else:
            ok, msg = SupplierController.add(
                self.user, name, contact, address, scat_id
            )

        if ok:
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


# ─────────────────────────────────────────────
# SUPPLIER CATEGORY DIALOG — styled
# ─────────────────────────────────────────────

class SupplierCategoryDialog(ctk.CTkToplevel):

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

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

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        ctk.CTkLabel(self, text="Manage Supplier Categories",
                     font=font_bold(16),
                     text_color=FG_PRIMARY).pack(pady=(16, 4))

        # ---- Card ----
        card = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        # ---- Add row ----
        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=14, pady=(14, 4))

        self.name_e = ctk.CTkEntry(add_row, height=36,
                                   placeholder_text="New category name",
                                   corner_radius=8,
                                   font=font(12),
                                   fg_color=BG_INPUT,
                                   border_color=BORDER,
                                   border_width=1)
        self.name_e.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(add_row, text="Add", width=70, height=36,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._add).pack(side="left")

        # ---- Description ----
        self.desc_e = ctk.CTkEntry(card, height=36,
                                   placeholder_text="Description (optional)",
                                   corner_radius=8,
                                   font=font(12),
                                   fg_color=BG_INPUT,
                                   border_color=BORDER,
                                   border_width=1)
        self.desc_e.pack(fill="x", padx=14, pady=(0, 10))

        # ---- List ----
        self.list_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=14, pady=(4, 14))

        self._load_categories()

    # ─────────────────────────────────────────────
    # LOAD
    # ─────────────────────────────────────────────

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

            row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=8)
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=c["name"], anchor="w",
                         font=font_bold(12),
                         text_color=FG_PRIMARY).pack(side="left", padx=12, pady=10)

            ctk.CTkLabel(row, text=c["description"] or "",
                         anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=(6, 12))

    # ─────────────────────────────────────────────
    # ADD
    # ─────────────────────────────────────────────

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