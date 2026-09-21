# ─────────────────────────────────────────────
# INVENTORY VIEW (softened 3F MiniMart branding)
# ─────────────────────────────────────────────

import os
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox

from controllers.auth_controller import AuthController
from controllers.inventory_controller import InventoryController
from controllers.supplier_controller import SupplierController
from utils import prepare_dialog_screen, pick_image_file, save_product_image
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BG_INPUT, BG_ROW_ALT, BORDER,
    FG_PRIMARY, FG_SECONDARY, FG_MUTED,
    BRAND_GREEN, BRAND_YELLOW,
    ACCENT, ACCENT_HOVER, SUCCESS, DANGER, DANGER_HOVER,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


# ─────────────────────────────────────────────
# INVENTORY VIEW
# ─────────────────────────────────────────────

class InventoryView(ctk.CTkFrame):

    # ---- Pagination size ----
    PAGE_SIZE = 10

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user
        self.categories = InventoryController.list_categories()
        self.selected_category_id = None
        self.show_archived = False
        self.search_query = ""

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

        ctk.CTkLabel(title_box, text="Inventory",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="Manage your products, stock levels, and categories",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ---- Right side: primary actions (admin only) ----
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

        ctk.CTkLabel(row1, text="Search",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        self.search_e = ctk.CTkEntry(
            row1,
            placeholder_text="Search by name, code, category, supplier...",
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

        # ---- Category filter ----
        ctk.CTkLabel(row1, text="Category",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.category_names = ["All Categories"] + [c["name"] for c in self.categories]
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

        # ---- Row 2: quick filters + count ----
        row2 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(row2, text="All Products",
                      width=120, height=32,
                      corner_radius=8,
                      font=font(11),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._load).pack(side="left", padx=(0, 6))

        ctk.CTkButton(row2, text="Low Stock Only",
                      width=120, height=32,
                      corner_radius=8,
                      font=font(11),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._load_low).pack(side="left")

        # ---- Results count ----
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

        self.list_frame = ctk.CTkScrollableFrame(
            list_card,
            fg_color="transparent",
        )
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
        """Enable/disable Prev/Next and update the label."""
        self.page_label.configure(
            text=f"Page {self.current_page} of {self.total_pages}"
        )

        # ---- Prev button ----
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

        # ---- Next button ----
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
    # SEARCH
    # ─────────────────────────────────────────────

    def _on_search_change(self, *args):
        self.search_query = self.search_var.get().strip().lower()
        self.current_page = 1     # ---- reset to page 1 on search ----
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
            for c in self.categories:
                if c["name"] == choice:
                    self.selected_category_id = c["category_id"]
                    break
        self.current_page = 1     # ---- reset to page 1 on category change ----
        self._load()

    def _toggle_archived(self):
        self.show_archived = self.archive_var.get()
        self.current_page = 1     # ---- reset to page 1 on toggle ----
        self._load()

    # ─────────────────────────────────────────────
    # LOAD
    # ─────────────────────────────────────────────

    def _load(self):
        # ---- Let the controller decide whether to include archived ----
        products = InventoryController.list_by_category(
            self.selected_category_id,
            include_archived=self.show_archived,
        )

        if self.search_query:
            products = [p for p in products if self._matches_search(p)]

        self._render(products)

    def _load_low(self):
        # ---- list_low_stock() already excludes archived products ----
        products = InventoryController.list_low_stock()

        # ---- Apply search filter only ----
        if self.search_query:
            products = [p for p in products if self._matches_search(p)]

        self.current_page = 1     # ---- reset on "Low Stock Only" ----
        self._render(products)

    def _matches_search(self, p):
        q = self.search_query
        fields = [
            (p["name"] or "").lower(),
            (p["product_code"] or "").lower(),
            (p["category_name"] or "").lower(),
            (p["supplier_name"] or "").lower(),
        ]
        return any(q in f for f in fields)

    # ─────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────

    def _render(self, products):
        for w in self.list_frame.winfo_children():
            w.destroy()

        # ---- Total count ----
        total = len(products)
        self.count_label.configure(text=f"{total} product(s)")

        # ---- Pagination math ----
        self.total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages

        start = (self.current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_products = products[start:end]

        # ---- Header ----
        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))

        cols = [
            ("",            50),
            ("Code",        80),
            ("Name",        130),
            ("Category",    100),
            ("Supplier",    120),
            ("Price",       70),
            ("Stock",       55),
            ("Status",      90),
            ("Date Added",  100),
        ]
        for text, width in cols:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

        # ---- Empty state ----
        if not page_products:
            msg = "No products match your search." if self.search_query \
                  else "No products to show."
            ctk.CTkLabel(self.list_frame, text=msg,
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            self._update_pager()
            return

        # ---- Rows ----
        for i, p in enumerate(page_products):
            self._render_row(p, i)

        # ---- Update pager ----
        self._update_pager()

    def _render_row(self, p, index=0):
        bg = BG_ROW_ALT if index % 2 else BG_CARD

        row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=6)
        row.pack(fill="x", pady=2)

        # ---- Thumbnail ----
        thumb = self._load_thumbnail(p["image_path"], size=(40, 40))
        if thumb:
            ctk.CTkLabel(row, image=thumb, text="",
                         width=50).pack(side="left", padx=3, pady=6)
        else:
            ctk.CTkLabel(row, text="—", width=50,
                         text_color=FG_MUTED).pack(side="left", padx=3)

        # ---- Code ----
        ctk.CTkLabel(row, text=p["product_code"] or "-",
                     width=80, anchor="w",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=3)

        # ---- Name ----
        ctk.CTkLabel(row, text=p["name"], width=130,
                     anchor="w",
                     font=font_bold(12),
                     text_color=FG_PRIMARY).pack(side="left", padx=3)

        # ---- Category ----
        ctk.CTkLabel(row, text=p["category_name"] or "-",
                     width=100, anchor="w",
                     font=font(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=3)

        # ---- Supplier ----
        ctk.CTkLabel(row, text=p["supplier_name"] or "-",
                     width=120, anchor="w",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=3)

        # ---- Price ----
        ctk.CTkLabel(row, text=f"₱{p['price']:.2f}",
                     width=70, anchor="w",
                     font=font(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=3)

        # ---- Stock (color-coded for low stock) ----
        stock_qty = p["stock_qty"]
        low_level = p["low_stock_level"] or 0

        if stock_qty <= 0:
            # ---- Out of stock ----
            stock_color = DANGER          # ---- red ----
        elif stock_qty <= low_level:
            # ---- Low stock ----
            stock_color = "#D97706"       # ---- amber / orange ----
        else:
            # ---- Healthy stock ----
            stock_color = FG_PRIMARY      # ---- normal text color ----

        ctk.CTkLabel(row, text=str(stock_qty),
                     width=55, anchor="w",
                     font=font_bold(11),
                     text_color=stock_color).pack(side="left", padx=3)

        # ---- Status ----
        if p["stock_qty"] > 0:
            status_text = "Available"
            status_color = SUCCESS
        else:
            status_text = "Not Available"
            status_color = DANGER

        status_badge = ctk.CTkFrame(row, fg_color="transparent")
        status_badge.pack(side="left", padx=3)

        ctk.CTkLabel(status_badge, text=status_text,
                     width=90,
                     font=font_bold(11),
                     text_color=status_color).pack()

        # ---- Date Added ----
        ctk.CTkLabel(row, text=(p["created_at"] or "")[:10],
                     width=100, anchor="w",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=3)

        # ---- Actions (admin only) ----
        if not AuthController.is_admin():
            return

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=4)

        if p["is_archived"]:
            ctk.CTkButton(actions, text="Restore", width=70, height=30,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=BRAND_GREEN, hover_color="#1E9040",
                          command=lambda prod=p: self._restore(prod)
                          ).pack(side="left", padx=2)
        else:
            ctk.CTkButton(actions, text="Restock", width=70, height=30,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=BRAND_YELLOW, hover_color="#E0B22E",
                          text_color="#0F172A",
                          command=lambda prod=p: self._restock(prod)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="Edit", width=60, height=30,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=ACCENT, hover_color=ACCENT_HOVER,
                          command=lambda prod=p: self._edit_dialog(prod)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="Archive", width=70, height=30,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=DANGER, hover_color=DANGER_HOVER,
                          command=lambda prod=p: self._archive(prod)
                          ).pack(side="left", padx=2)

    # ─────────────────────────────────────────────
    # THUMBNAIL LOADER
    # ─────────────────────────────────────────────

    def _load_thumbnail(self, image_path, size=(40, 40)):
        if not image_path or not os.path.exists(image_path):
            return None
        try:
            img = Image.open(image_path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception:
            return None

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def _restock(self, product):
        RestockDialog(self.winfo_toplevel(), self.user, product,
                      on_save=self._load)

    def _archive(self, product):
        confirm = messagebox.askyesno(
            "Archive Product",
            f"Archive '{product['name']}'?\n\n"
            "Archived products are hidden from POS and inventory but kept in history."
        )
        if not confirm:
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

    # ─────────────────────────────────────────────
    # DIALOGS
    # ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# PRODUCT DIALOG (styled)
# ─────────────────────────────────────────────

class ProductDialog(ctk.CTkToplevel):

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user, product, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.product = product
        self.on_save = on_save
        self.title("Product")
        self.geometry("520x600")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)

        self.suppliers = SupplierController.list_suppliers()
        self.categories = InventoryController.list_categories()

        self.new_image_source = None
        self.current_image_path = (product["image_path"] if product else None)
        self.preview_image = None

        self._build()
        prepare_dialog_screen(self, self.parent)

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        p = self.product

        ctk.CTkLabel(self,
                     text="Edit Product" if p else "New Product",
                     font=font_bold(16),
                     text_color=FG_PRIMARY).pack(pady=(16, 4))

        card = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(14, 6))

        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left", padx=(0, 12))

        self.preview_label = ctk.CTkLabel(left, text="No image",
                                          width=140, height=140,
                                          fg_color=BG_INPUT,
                                          corner_radius=8,
                                          font=font(11),
                                          text_color=FG_MUTED)
        self.preview_label.pack()

        if p and p["image_path"]:
            self._set_preview(p["image_path"])

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(pady=(6, 0))
        ctk.CTkButton(btn_row, text="Choose", width=65, height=28,
                      corner_radius=6,
                      font=font(11),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._choose_image).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Clear", width=65, height=28,
                      corner_radius=6,
                      font=font(11),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._clear_image).pack(side="left", padx=2)

        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        if p:
            ctk.CTkLabel(right, text="CODE", anchor="w",
                         font=font_bold(10),
                         text_color=FG_SECONDARY).pack(fill="x", pady=(0, 4))
            code_e = ctk.CTkEntry(right, height=32,
                                  corner_radius=6,
                                  font=font(12),
                                  fg_color=BG_INPUT,
                                  border_color=BORDER,
                                  border_width=1)
            code_e.insert(0, p["product_code"] or "")
            code_e.configure(state="disabled")
            code_e.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(right, text="NAME", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", pady=(0, 4))
        self.name_e = ctk.CTkEntry(right, height=32,
                                   corner_radius=6,
                                   font=font(12),
                                   fg_color=BG_INPUT,
                                   border_color=BORDER,
                                   border_width=1)
        self.name_e.pack(fill="x", pady=(0, 8))
        if p: self.name_e.insert(0, p["name"])

        ctk.CTkLabel(right, text="PRICE", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", pady=(0, 4))
        self.price_e = ctk.CTkEntry(right, height=32,
                                    corner_radius=6,
                                    font=font(12),
                                    fg_color=BG_INPUT,
                                    border_color=BORDER,
                                    border_width=1)
        self.price_e.pack(fill="x")
        if p: self.price_e.insert(0, str(p["price"]))

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=(8, 4))

        left_col = ctk.CTkFrame(grid, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkLabel(left_col, text="STOCK QUANTITY", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", pady=(0, 4))
        self.stock_e = ctk.CTkEntry(left_col, height=32,
                                    corner_radius=6,
                                    font=font(12),
                                    fg_color=BG_INPUT,
                                    border_color=BORDER,
                                    border_width=1)
        self.stock_e.pack(fill="x")
        if p: self.stock_e.insert(0, str(p["stock_qty"]))
        else: self.stock_e.insert(0, "0")

        right_col = ctk.CTkFrame(grid, fg_color="transparent")
        right_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(right_col, text="LOW STOCK LEVEL", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", pady=(0, 4))
        self.low_e = ctk.CTkEntry(right_col, height=32,
                                  corner_radius=6,
                                  font=font(12),
                                  fg_color=BG_INPUT,
                                  border_color=BORDER,
                                  border_width=1)
        self.low_e.pack(fill="x")
        if p: self.low_e.insert(0, str(p["low_stock_level"]))
        else: self.low_e.insert(0, "10")

        cat_row = ctk.CTkFrame(card, fg_color="transparent")
        cat_row.pack(fill="x", padx=14, pady=(8, 4))

        ctk.CTkLabel(cat_row, text="CATEGORY", width=100, anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(side="left")

        cat_names = [c["name"] for c in self.categories] or ["(No categories)"]
        self.category_var = ctk.StringVar(
            value=p["category_name"] if p and p["category_name"] else cat_names[0]
        )
        self.category_menu = ctk.CTkOptionMenu(
            cat_row, values=cat_names, variable=self.category_var,
            width=270, height=32,
            corner_radius=6,
            font=font(12),
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=NEUTRAL,
            text_color=FG_PRIMARY,
        )
        self.category_menu.pack(side="left", padx=(0, 6))
        ctk.CTkButton(cat_row, text="+", width=32, height=32,
                      corner_radius=6,
                      font=font_bold(14),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._quick_add_category).pack(side="left")

        sup_row = ctk.CTkFrame(card, fg_color="transparent")
        sup_row.pack(fill="x", padx=14, pady=(4, 4))

        ctk.CTkLabel(sup_row, text="SUPPLIER", width=100, anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(side="left")

        sup_names = [s["name"] for s in self.suppliers] or ["(No suppliers)"]
        self.supplier_var = ctk.StringVar(
            value=p["supplier_name"] if p and p["supplier_name"] else sup_names[0]
        )
        ctk.CTkOptionMenu(sup_row, values=sup_names, variable=self.supplier_var,
                          width=310, height=32,
                          corner_radius=6,
                          font=font(12),
                          fg_color=BG_INPUT,
                          button_color=BG_INPUT,
                          button_hover_color=NEUTRAL,
                          text_color=FG_PRIMARY).pack(side="left")

        ctk.CTkButton(card, text="Save Product",
                      width=220, height=40,
                      corner_radius=8,
                      font=font_bold(13),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._save).pack(pady=(16, 16))

    # ─────────────────────────────────────────────
    # PICTURE HELPERS
    # ─────────────────────────────────────────────

    def _choose_image(self):
        path = pick_image_file()
        if not path:
            return
        self.new_image_source = path
        self._set_preview(path)

    def _clear_image(self):
        self.new_image_source = None
        self.current_image_path = None
        self.preview_image = None
        self.preview_label.configure(image=None, text="No image")

    def _set_preview(self, path):
        try:
            img = Image.open(path)
            self.preview_image = ctk.CTkImage(
                light_image=img, dark_image=img, size=(140, 140)
            )
            self.preview_label.configure(image=self.preview_image, text="")
        except Exception:
            self.preview_label.configure(image=None, text="Invalid image")

    # ─────────────────────────────────────────────
    # QUICK ADD CATEGORY
    # ─────────────────────────────────────────────

    def _quick_add_category(self):
        prompt = ctk.CTkToplevel(self)
        prompt.title("Quick Add Category")
        prompt.geometry("340x200")
        prompt.resizable(False, False)
        prompt.configure(fg_color=BG_MAIN)

        ctk.CTkLabel(prompt, text="New Category",
                     font=font_bold(14),
                     text_color=FG_PRIMARY).pack(pady=(20, 4))

        name_e = ctk.CTkEntry(prompt, width=240, height=34,
                              corner_radius=6,
                              font=font(12),
                              fg_color=BG_INPUT,
                              border_color=BORDER,
                              border_width=1)
        name_e.pack(pady=(8, 16))
        name_e.focus_set()

        def save():
            name = name_e.get().strip()
            if not name:
                messagebox.showerror("Error", "Category name is required.")
                return
            ok, msg = InventoryController.add_category(self.user, name)
            if not ok:
                messagebox.showerror("Error", msg)
                return
            self.categories = InventoryController.list_categories()
            self.category_menu.configure(values=[c["name"] for c in self.categories])
            self.category_var.set(name)
            prompt.destroy()

        ctk.CTkButton(prompt, text="Save", width=240, height=36,
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
        try:
            price = float(self.price_e.get())
            stock = int(self.stock_e.get())
            low = int(self.low_e.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric input.")
            return

        category_id = None
        for c in self.categories:
            if c["name"] == self.category_var.get():
                category_id = c["category_id"]
                break

        supplier_id = None
        for s in self.suppliers:
            if s["name"] == self.supplier_var.get():
                supplier_id = s["supplier_id"]
                break

        if category_id is None:
            messagebox.showerror("Error", "Please select a category.")
            return
        if supplier_id is None:
            messagebox.showerror("Error", "Please select a supplier.")
            return

        if self.new_image_source:
            self.current_image_path = save_product_image(self.new_image_source)

        if self.product:
            ok, msg = InventoryController.update(
                self.user, self.product["product_id"],
                name, price, stock, low, supplier_id, category_id,
                self.current_image_path
            )
        else:
            ok, msg = InventoryController.add(
                self.user, name, price, stock, low, supplier_id, category_id,
                self.current_image_path
            )

        if ok:
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


# ─────────────────────────────────────────────
# RESTOCK DIALOG (styled)
# ─────────────────────────────────────────────

class RestockDialog(ctk.CTkToplevel):

    def __init__(self, parent, user, product, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.product = product
        self.on_save = on_save
        self.title("Restock Product")
        self.geometry("380x320")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        p = self.product

        ctk.CTkLabel(self, text="Restock Product",
                     font=font_bold(16),
                     text_color=FG_PRIMARY).pack(pady=(18, 4))

        ctk.CTkLabel(self, text=f"{p['name']}  ({p['product_code']})",
                     font=font(12),
                     text_color=FG_SECONDARY).pack(pady=2)

        info = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=10,
                            border_width=1,
                            border_color=BORDER)
        info.pack(fill="x", padx=20, pady=(10, 6))

        ctk.CTkLabel(info, text="Current Stock",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(pady=(12, 0))
        ctk.CTkLabel(info, text=str(p["stock_qty"]),
                     font=font_bold(24),
                     text_color=ACCENT).pack(pady=(0, 12))

        ctk.CTkLabel(self, text="QUANTITY TO ADD",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(pady=(8, 4))

        self.qty_e = ctk.CTkEntry(self, width=200, height=38,
                                  corner_radius=8,
                                  font=font(14),
                                  fg_color=BG_INPUT,
                                  border_color=BORDER,
                                  border_width=1,
                                  justify="center")
        self.qty_e.pack()
        self.qty_e.insert(0, "10")
        self.qty_e.focus_set()
        self.qty_e.select_range(0, "end")

        ctk.CTkButton(self, text="Restock",
                      width=200, height=40,
                      corner_radius=8,
                      font=font_bold(13),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._save).pack(pady=(18, 16))

    def _save(self):
        try:
            qty = int(self.qty_e.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter a valid positive number.")
            return

        ok, msg = InventoryController.restock(
            self.user, self.product["product_id"], qty
        )
        if ok:
            messagebox.showinfo("Restocked", msg)
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


# ─────────────────────────────────────────────
# CATEGORY DIALOG (styled)
# ─────────────────────────────────────────────

class CategoryDialog(ctk.CTkToplevel):

    def __init__(self, parent, user, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.on_save = on_save
        self.title("Manage Categories")
        self.geometry("500x480")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        ctk.CTkLabel(self, text="Manage Categories",
                     font=font_bold(16),
                     text_color=FG_PRIMARY).pack(pady=(16, 4))

        card = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=(8, 16))

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

        self.desc_e = ctk.CTkEntry(card, height=36,
                                   placeholder_text="Description (optional)",
                                   corner_radius=8,
                                   font=font(12),
                                   fg_color=BG_INPUT,
                                   border_color=BORDER,
                                   border_width=1)
        self.desc_e.pack(fill="x", padx=14, pady=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=14, pady=(4, 14))

        self._load_categories()

    def _load_categories(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        cats = InventoryController.list_categories()

        if not cats:
            ctk.CTkLabel(self.list_frame,
                         text="No categories yet.",
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=20)
            return

        for c in cats:
            row = ctk.CTkFrame(self.list_frame, fg_color=BG_ROW_ALT,
                               corner_radius=8)
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=c["name"], anchor="w",
                         font=font_bold(12),
                         text_color=FG_PRIMARY).pack(side="left", padx=12, pady=10)

            ctk.CTkLabel(row, text=c["description"] or "",
                         anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=(6, 12))

    def _add(self):
        name = self.name_e.get().strip()
        desc = self.desc_e.get().strip()

        if not name:
            messagebox.showerror("Error", "Category name is required.")
            return

        ok, msg = InventoryController.add_category(self.user, name, desc)
        if not ok:
            messagebox.showerror("Error", msg)
            return

        self.name_e.delete(0, "end")
        self.desc_e.delete(0, "end")
        self._load_categories()
        self.on_save()