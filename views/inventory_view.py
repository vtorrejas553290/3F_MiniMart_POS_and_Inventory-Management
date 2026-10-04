# ─────────────────────────────────────────────
# INVENTORY VIEW (batch-aggregated)
# ─────────────────────────────────────────────

from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

from controllers.auth_controller import AuthController
from controllers.inventory_controller import InventoryController
from views.product_dialogs import (
    ProductDialog, RestockDialog, BatchesDialog, CategoryDialog,
)
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BG_INPUT, BG_ROW_ALT, BORDER,
    FG_PRIMARY, FG_SECONDARY, FG_MUTED,
    BRAND_GREEN, BRAND_YELLOW,
    ACCENT, ACCENT_HOVER, SUCCESS, DANGER, DANGER_HOVER,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


class InventoryView(ctk.CTkFrame):

    PAGE_SIZE = 10

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user
        self.categories = InventoryController.list_categories()
        self.selected_category_id = None
        self.show_archived = False
        self.search_query = ""

        self.current_page = 1
        self.total_pages = 1

        self._build()
        self._load()

    def _build(self):
        # ---- Header ----
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box, text="Inventory",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="Manage your products, stock levels, and batches",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        if AuthController.is_admin():
            actions = ctk.CTkFrame(header_frame, fg_color="transparent")
            actions.pack(side="right")

            ctk.CTkButton(actions, text="+ Add Product",
                          height=38, corner_radius=8,
                          font=font_bold(12),
                          fg_color=ACCENT, hover_color=ACCENT_HOVER,
                          command=self._add_dialog).pack(side="right", padx=(6, 0))

            ctk.CTkButton(actions, text="+ Add Category",
                          height=38, corner_radius=8,
                          font=font_bold(12),
                          fg_color=BRAND_GREEN, hover_color="#1E9040",
                          command=self._add_category_dialog).pack(side="right", padx=(6, 0))

        # ---- Filter card ----
        filter_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                   corner_radius=12, border_width=1,
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
            placeholder_text="Search by name, brand, code, category, supplier...",
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

        self.category_names = ["All Categories"] + [c["name"] for c in self.categories]
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

        ctk.CTkButton(row2, text="All Products",
                      width=120, height=32, corner_radius=8, font=font(11),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._load).pack(side="left", padx=(0, 6))

        ctk.CTkButton(row2, text="Low Stock Only",
                      width=120, height=32, corner_radius=8, font=font(11),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._load_low).pack(side="left")

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

    # ---- Pagination ----
    def _change_page(self, delta):
        new_page = self.current_page + delta
        if 1 <= new_page <= self.total_pages:
            self.current_page = new_page
            self._load()

    def _update_pager(self):
        self.page_label.configure(text=f"Page {self.current_page} of {self.total_pages}")
        if self.current_page <= 1:
            self.prev_btn.configure(state="disabled", fg_color=BG_INPUT,
                                    text_color=FG_MUTED)
        else:
            self.prev_btn.configure(state="normal", fg_color=NEUTRAL,
                                    text_color=NEUTRAL_TEXT)
        if self.current_page >= self.total_pages:
            self.next_btn.configure(state="disabled", fg_color=BG_INPUT,
                                    text_color=FG_MUTED)
        else:
            self.next_btn.configure(state="normal", fg_color=NEUTRAL,
                                    text_color=NEUTRAL_TEXT)

    # ---- Filters ----
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
            for c in self.categories:
                if c["name"] == choice:
                    self.selected_category_id = c["category_id"]
                    break
        self.current_page = 1
        self._load()

    def _toggle_archived(self):
        self.show_archived = self.archive_var.get()
        self.current_page = 1
        self._load()

    # ---- Load ----
    def _load(self):
        products = InventoryController.list_by_category(
            self.selected_category_id,
            include_archived=self.show_archived,
        )
        if self.search_query:
            products = [p for p in products if self._matches_search(p)]
        self._render(products)

    def _load_low(self):
        products = InventoryController.list_low_stock()
        if self.search_query:
            products = [p for p in products if self._matches_search(p)]
        self.current_page = 1
        self._render(products)

    def _matches_search(self, p):
        q = self.search_query
        fields = [
            (p["name"] or "").lower(),
            (p["brand"] or "").lower(),
            (p["size"] or "").lower(),
            (p["product_code"] or "").lower(),
            (p["category_name"] or "").lower(),
            (p["supplier_name"] or "").lower(),
        ]
        return any(q in f for f in fields)

    # ---- Render ----
    def _render(self, products):
        for w in self.list_frame.winfo_children():
            w.destroy()

        total = len(products)
        self.count_label.configure(text=f"{total} product(s)")

        self.total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages

        start = (self.current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_products = products[start:end]

        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))

        cols = [
            ("Code",        90),
            ("Name",        200),
            ("Unit",        50),
            ("Category",    100),
            ("Supplier",    120),
            ("Price",       75),
            ("Stock",       55),
            ("Expires",     100),
            ("Status",      90),
        ]
        for text, width in cols:
            ctk.CTkLabel(header, text=text, width=width, anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

        if not page_products:
            msg = "No products match your search." if self.search_query \
                  else "No products to show."
            ctk.CTkLabel(self.list_frame, text=msg, font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            self._update_pager()
            return

        for i, p in enumerate(page_products):
            self._render_row(p, i)

        self._update_pager()

    def _render_row(self, p, index=0):
        bg = BG_ROW_ALT if index % 2 else BG_CARD
        row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=6)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=p["product_code"] or "-",
                     width=90, anchor="w", font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=3, pady=6)

        display_name = self._display_name(p)
        ctk.CTkLabel(row, text=display_name, width=200, anchor="w",
                     font=font_bold(12),
                     text_color=FG_PRIMARY).pack(side="left", padx=3)

        ctk.CTkLabel(row, text=p["unit"] or "-",
                     width=50, anchor="w", font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=3)

        ctk.CTkLabel(row, text=p["category_name"] or "-",
                     width=100, anchor="w", font=font(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=3)

        ctk.CTkLabel(row, text=p["supplier_name"] or "-",
                     width=120, anchor="w", font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=3)

        ctk.CTkLabel(row, text=f"₱{p['price']:.2f}",
                     width=75, anchor="w", font=font(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=3)

        # ---- Stock color ----
        stock_qty = p["stock_qty"]
        low_level = p["low_stock_level"] or 0

        if stock_qty <= 0:
            stock_color = DANGER
        elif stock_qty <= low_level:
            stock_color = "#D97706"
        else:
            stock_color = FG_PRIMARY

        ctk.CTkLabel(row, text=str(stock_qty),
                     width=55, anchor="w", font=font_bold(11),
                     text_color=stock_color).pack(side="left", padx=3)

        # ---- Earliest expiration ----
        exp_text, exp_color = self._expiration_display(p["earliest_expiration"])
        ctk.CTkLabel(row, text=exp_text, width=100, anchor="w",
                     font=font(11),
                     text_color=exp_color).pack(side="left", padx=3)

        # ---- Status ----
        if stock_qty > 0:
            status_text, status_color = "Available", SUCCESS
        else:
            status_text, status_color = "Not Available", DANGER

        ctk.CTkLabel(row, text=status_text, width=90, anchor="w",
                     font=font_bold(11),
                     text_color=status_color).pack(side="left", padx=3)

        # ---- Actions ----
        if not AuthController.is_admin():
            return

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=4)

        if p["is_archived"]:
            ctk.CTkButton(actions, text="Restore", width=70, height=28,
                          corner_radius=6, font=font_bold(11),
                          fg_color=BRAND_GREEN, hover_color="#1E9040",
                          command=lambda prod=p: self._restore(prod)
                          ).pack(side="left", padx=2)
        else:
            ctk.CTkButton(actions, text="Batches", width=70, height=28,
                          corner_radius=6, font=font_bold(11),
                          fg_color="#7C3AED", hover_color="#6D28D9",
                          command=lambda prod=p: self._view_batches(prod)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="Restock", width=70, height=28,
                          corner_radius=6, font=font_bold(11),
                          fg_color=BRAND_YELLOW, hover_color="#E0B22E",
                          text_color="#0F172A",
                          command=lambda prod=p: self._restock(prod)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="Edit", width=55, height=28,
                          corner_radius=6, font=font_bold(11),
                          fg_color=ACCENT, hover_color=ACCENT_HOVER,
                          command=lambda prod=p: self._edit_dialog(prod)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="Archive", width=65, height=28,
                          corner_radius=6, font=font_bold(11),
                          fg_color=DANGER, hover_color=DANGER_HOVER,
                          command=lambda prod=p: self._archive(prod)
                          ).pack(side="left", padx=2)

    @staticmethod
    def _display_name(p):
        parts = [p["brand"], p["name"], p["size"]]
        return " ".join(part for part in parts if part)

    def _expiration_display(self, expiration_date):
        if not expiration_date:
            return "—", FG_MUTED
        try:
            exp = datetime.strptime(expiration_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return expiration_date, FG_MUTED

        days_left = (exp - datetime.now().date()).days
        if days_left < 0:
            return f"{expiration_date} ✗", DANGER
        if days_left <= 30:
            return f"{expiration_date} ({days_left}d)", "#D97706"
        return expiration_date, FG_SECONDARY

    # ---- Actions ----
    def _restock(self, product):
        RestockDialog(self.winfo_toplevel(), self.user, product,
                      on_save=self._load)

    def _view_batches(self, product):
        BatchesDialog(self.winfo_toplevel(), self.user, product,
                      on_save=self._load)

    def _archive(self, product):
        if not messagebox.askyesno(
            "Archive Product",
            f"Archive '{product['name']}'?\n\n"
            "Archived products are hidden from POS and inventory but kept in history."
        ):
            return
        ok, msg = InventoryController.archive(
            self.user, product["product_id"], product["name"]
        )
        if ok:
            messagebox.showinfo("Archived", f"'{product['name']}' archived.")
            self._load()
        else:
            messagebox.showerror("Error", msg)

    def _restore(self, product):
        ok, msg = InventoryController.unarchive(
            self.user, product["product_id"], product["name"]
        )
        if ok:
            self._load()
        else:
            messagebox.showerror("Error", msg)

    # ---- Dialogs ----
    def _add_dialog(self):
        ProductDialog(self.winfo_toplevel(), self.user, None,
                      on_save=self._after_product_saved)

    def _edit_dialog(self, product):
        ProductDialog(self.winfo_toplevel(), self.user, product,
                      on_save=self._after_product_saved)

    def _add_category_dialog(self):
        CategoryDialog(self.winfo_toplevel(), self.user,
                       on_save=self._refresh_categories)

    def _after_product_saved(self):
        self._load()

    def _refresh_categories(self):
        self.categories = InventoryController.list_categories()
        self.category_names = ["All Categories"] + [c["name"] for c in self.categories]
        self.category_menu.configure(values=self.category_names)
        self._load()