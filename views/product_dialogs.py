# ─────────────────────────────────────────────
# PRODUCT DIALOGS (Product / Restock / Batches / Category / EditBatch)
# ─────────────────────────────────────────────

from datetime import datetime
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox

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
# PRODUCT DIALOG (add / edit)
# ─────────────────────────────────────────────

class ProductDialog(ctk.CTkToplevel):

    def __init__(self, parent, user, product, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.product = product
        self.on_save = on_save
        self.title("Product")
        self.geometry("520x660")
        self.resizable(True, True)
        self.minsize(480, 500)
        self.configure(fg_color=BG_MAIN)

        self.suppliers = SupplierController.list_suppliers()
        self.categories = InventoryController.list_categories()

        self.new_image_source = None
        self.current_image_path = (product["image_path"] if product else None)
        self.preview_image = None

        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        p = self.product
        is_edit = p is not None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(header,
                     text="Edit Product" if is_edit else "New Product",
                     font=font_bold(15),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(side="left")

        ctk.CTkButton(header, text="✕",
                      width=30, height=30,
                      corner_radius=6,
                      font=font_bold(13),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self.destroy).pack(side="right")

        card = ctk.CTkScrollableFrame(self, fg_color=BG_CARD,
                                      corner_radius=10,
                                      border_width=1,
                                      border_color=BORDER)
        card.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        # ---- Image row ----
        img_row = ctk.CTkFrame(card, fg_color="transparent")
        img_row.pack(fill="x", padx=12, pady=(10, 6))

        self.preview_label = ctk.CTkLabel(img_row, text="No image",
                                          width=90, height=90,
                                          fg_color=BG_INPUT,
                                          corner_radius=8,
                                          font=font(10),
                                          text_color=FG_MUTED)
        self.preview_label.pack(side="left")

        if p and p["image_path"]:
            self._set_preview(p["image_path"])

        btn_col = ctk.CTkFrame(img_row, fg_color="transparent")
        btn_col.pack(side="left", padx=(10, 0), fill="y")

        ctk.CTkButton(btn_col, text="Choose Image", width=120, height=30,
                      corner_radius=6, font=font(11),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._choose_image).pack(pady=(4, 4))
        ctk.CTkButton(btn_col, text="Clear Image", width=120, height=30,
                      corner_radius=6, font=font(11),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._clear_image).pack()

        # ---- Code (edit only) ----
        if is_edit:
            ctk.CTkLabel(card, text="CODE", anchor="w",
                         font=font_bold(10),
                         text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(6, 3))
            code_e = ctk.CTkEntry(card, height=30, corner_radius=6,
                                  font=font(12), fg_color=BG_INPUT,
                                  border_color=BORDER, border_width=1)
            code_e.insert(0, p["product_code"] or "")
            code_e.configure(state="disabled")
            code_e.pack(fill="x", padx=12)

        # ---- Name ----
        ctk.CTkLabel(card, text="NAME", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(6, 3))
        self.name_e = ctk.CTkEntry(card, height=30, corner_radius=6,
                                   font=font(12), fg_color=BG_INPUT,
                                   border_color=BORDER, border_width=1)
        self.name_e.pack(fill="x", padx=12)
        if p: self.name_e.insert(0, p["name"])

        # ---- Brand ----
        ctk.CTkLabel(card, text="BRAND", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(6, 3))
        self.brand_e = ctk.CTkEntry(card, height=30, corner_radius=6,
                                    font=font(12), fg_color=BG_INPUT,
                                    border_color=BORDER, border_width=1)
        self.brand_e.pack(fill="x", padx=12)
        if p and p["brand"]: self.brand_e.insert(0, p["brand"])

        # ---- Size ----
        ctk.CTkLabel(card, text="SIZE  (e.g. 100g, 500ml, 12 pcs)", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(6, 3))
        self.size_e = ctk.CTkEntry(card, height=30, corner_radius=6,
                                   font=font(12), fg_color=BG_INPUT,
                                   border_color=BORDER, border_width=1)
        self.size_e.pack(fill="x", padx=12)
        if p and p["size"]: self.size_e.insert(0, p["size"])

        # ---- Price + Cost ----
        price_row = ctk.CTkFrame(card, fg_color="transparent")
        price_row.pack(fill="x", padx=12, pady=(6, 3))

        price_col = ctk.CTkFrame(price_row, fg_color="transparent")
        price_col.pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkLabel(price_col, text="SELLING PRICE", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", pady=(0, 3))
        self.price_e = ctk.CTkEntry(price_col, height=30, corner_radius=6,
                                    font=font(12), fg_color=BG_INPUT,
                                    border_color=BORDER, border_width=1)
        self.price_e.pack(fill="x")
        if p: self.price_e.insert(0, str(p["price"]))

        cost_col = ctk.CTkFrame(price_row, fg_color="transparent")
        cost_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(cost_col, text="COST PRICE", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", pady=(0, 3))
        self.cost_e = ctk.CTkEntry(cost_col, height=30, corner_radius=6,
                                   font=font(12), fg_color=BG_INPUT,
                                   border_color=BORDER, border_width=1)
        self.cost_e.pack(fill="x")
        if p and p["cost_price"] is not None:
            self.cost_e.insert(0, str(p["cost_price"]))
        else:
            self.cost_e.insert(0, "0")

        # ---- Low stock ----
        ctk.CTkLabel(card, text="LOW STOCK LEVEL", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(6, 3))
        self.low_e = ctk.CTkEntry(card, height=30, corner_radius=6,
                                  font=font(12), fg_color=BG_INPUT,
                                  border_color=BORDER, border_width=1)
        self.low_e.pack(fill="x", padx=12)
        if p: self.low_e.insert(0, str(p["low_stock_level"]))
        else: self.low_e.insert(0, "10")

        # ---- Unit ----
        ctk.CTkLabel(card, text="UNIT", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(6, 3))

        unit_values = ["pc", "pack", "box", "kg", "g", "L", "mL", "sack"]
        self.unit_var = ctk.StringVar(
            value=(p["unit"] if p and p["unit"] else "pc")
        )
        ctk.CTkOptionMenu(card, values=unit_values, variable=self.unit_var,
                          height=30, corner_radius=6, font=font(12),
                          fg_color=BG_INPUT, button_color=BG_INPUT,
                          button_hover_color=NEUTRAL,
                          text_color=FG_PRIMARY).pack(fill="x", padx=12)

        # ---- INITIAL STOCK + EXPIRY (add mode only) ----
        if not is_edit:
            ctk.CTkLabel(card,
                         text="INITIAL STOCK  (creates the first batch)",
                         anchor="w",
                         font=font_bold(10),
                         text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(6, 3))

            init_row = ctk.CTkFrame(card, fg_color="transparent")
            init_row.pack(fill="x", padx=12)

            stock_col = ctk.CTkFrame(init_row, fg_color="transparent")
            stock_col.pack(side="left", fill="x", expand=True, padx=(0, 4))

            ctk.CTkLabel(stock_col, text="QUANTITY", anchor="w",
                         font=font_bold(10),
                         text_color=FG_SECONDARY).pack(fill="x", pady=(0, 3))
            self.stock_e = ctk.CTkEntry(stock_col, height=30, corner_radius=6,
                                        font=font(12), fg_color=BG_INPUT,
                                        border_color=BORDER, border_width=1)
            self.stock_e.pack(fill="x")
            self.stock_e.insert(0, "0")

            exp_col = ctk.CTkFrame(init_row, fg_color="transparent")
            exp_col.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(exp_col, text="EXPIRATION (optional)", anchor="w",
                         font=font_bold(10),
                         text_color=FG_SECONDARY).pack(fill="x", pady=(0, 3))
            self.exp_e = ctk.CTkEntry(exp_col, height=30, corner_radius=6,
                                      font=font(12), fg_color=BG_INPUT,
                                      border_color=BORDER, border_width=1,
                                      placeholder_text="YYYY-MM-DD")
            self.exp_e.pack(fill="x")
        else:
            self.stock_e = None
            self.exp_e = None

            ctk.CTkLabel(card,
                         text=("Stock and expiration are managed per batch — "
                               "use Restock or View Batches on the inventory row."),
                         anchor="w", wraplength=460,
                         font=font(10),
                         text_color=FG_MUTED).pack(fill="x", padx=12, pady=(8, 0))

        # ---- Category ----
        ctk.CTkLabel(card, text="CATEGORY", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(6, 3))

        cat_row = ctk.CTkFrame(card, fg_color="transparent")
        cat_row.pack(fill="x", padx=12)

        cat_names = [c["name"] for c in self.categories] or ["(No categories)"]
        self.category_var = ctk.StringVar(
            value=p["category_name"] if p and p["category_name"] else cat_names[0]
        )
        self.category_menu = ctk.CTkOptionMenu(
            cat_row, values=cat_names, variable=self.category_var,
            height=30, corner_radius=6, font=font(12),
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=NEUTRAL, text_color=FG_PRIMARY,
        )
        self.category_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(cat_row, text="+", width=30, height=30,
                      corner_radius=6,
                      font=font_bold(13),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._quick_add_category).pack(side="left")

        # ---- Supplier ----
        ctk.CTkLabel(card, text="SUPPLIER", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=12, pady=(6, 3))

        sup_names = [s["name"] for s in self.suppliers] or ["(No suppliers)"]
        self.supplier_var = ctk.StringVar(
            value=p["supplier_name"] if p and p["supplier_name"] else sup_names[0]
        )
        ctk.CTkOptionMenu(card, values=sup_names, variable=self.supplier_var,
                          height=30, corner_radius=6, font=font(12),
                          fg_color=BG_INPUT, button_color=BG_INPUT,
                          button_hover_color=NEUTRAL,
                          text_color=FG_PRIMARY).pack(fill="x", padx=12)

        # ---- Save ----
        ctk.CTkButton(card, text="Save Product",
                      height=38, corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._save).pack(fill="x", padx=12, pady=(14, 12))

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
                light_image=img, dark_image=img, size=(90, 90)
            )
            self.preview_label.configure(image=self.preview_image, text="")
        except Exception:
            self.preview_label.configure(image=None, text="Invalid image")

    def _quick_add_category(self):
        prompt = ctk.CTkToplevel(self)
        prompt.title("Quick Add Category")
        prompt.geometry("320x180")
        prompt.resizable(False, False)
        prompt.configure(fg_color=BG_MAIN)

        ctk.CTkLabel(prompt, text="New Category",
                     font=font_bold(13),
                     text_color=FG_PRIMARY).pack(pady=(16, 4))

        name_e = ctk.CTkEntry(prompt, width=220, height=32,
                              corner_radius=6, font=font(12),
                              fg_color=BG_INPUT, border_color=BORDER,
                              border_width=1)
        name_e.pack(pady=(6, 12))
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

        ctk.CTkButton(prompt, text="Save", width=220, height=34,
                      corner_radius=8, font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=save).pack(pady=(0, 16))
        prepare_dialog_screen(prompt, self)

    def _save(self):
        name = self.name_e.get().strip()
        brand = self.brand_e.get().strip() or None
        size = self.size_e.get().strip() or None
        unit = self.unit_var.get().strip() or "pc"

        if not name:
            messagebox.showerror("Error", "Product name is required.")
            return

        try:
            price = float(self.price_e.get())
            low = int(self.low_e.get())
            cost = float(self.cost_e.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric input.")
            return

        if price < 0 or cost < 0 or low < 0:
            messagebox.showerror("Error", "Values cannot be negative.")
            return

        initial_stock = 0
        expiration_date = None
        if self.product is None:
            try:
                initial_stock = int(self.stock_e.get() or 0)
            except ValueError:
                messagebox.showerror("Error", "Invalid initial stock.")
                return
            if initial_stock < 0:
                messagebox.showerror("Error", "Stock cannot be negative.")
                return

            expiration_date = (self.exp_e.get().strip() or None)
            if expiration_date:
                try:
                    datetime.strptime(expiration_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror(
                        "Error",
                        "Expiration date must be in YYYY-MM-DD format."
                    )
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
                name, price, low, supplier_id, category_id,
                self.current_image_path,
                brand=brand, size=size, unit=unit, cost_price=cost,
            )
        else:
            ok, msg = InventoryController.add(
                self.user, name, price, initial_stock, low,
                supplier_id, category_id,
                self.current_image_path,
                brand=brand, size=size, unit=unit, cost_price=cost,
                expiration_date=expiration_date,
            )

        if ok:
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


# ─────────────────────────────────────────────
# RESTOCK DIALOG
# ─────────────────────────────────────────────

class RestockDialog(ctk.CTkToplevel):

    def __init__(self, parent, user, product, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.product = product
        self.on_save = on_save
        self.title("Restock Product")
        self.geometry("400x420")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        p = self.product

        ctk.CTkLabel(self, text="Restock Product",
                     font=font_bold(15),
                     text_color=FG_PRIMARY).pack(pady=(16, 4))

        ctk.CTkLabel(self, text=f"{p['name']}  ({p['product_code']})",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(pady=2)

        info = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=10,
                            border_width=1, border_color=BORDER)
        info.pack(fill="x", padx=20, pady=(8, 6))

        ctk.CTkLabel(info, text="Current Sellable Stock",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(pady=(10, 0))
        ctk.CTkLabel(info, text=f"{p['stock_qty']} {p['unit'] or ''}".strip(),
                     font=font_bold(22),
                     text_color=ACCENT).pack(pady=(0, 10))

        ctk.CTkLabel(self, text="QUANTITY TO ADD",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(pady=(6, 4))
        self.qty_e = ctk.CTkEntry(self, width=220, height=36,
                                  corner_radius=8, font=font(13),
                                  fg_color=BG_INPUT, border_color=BORDER,
                                  border_width=1, justify="center")
        self.qty_e.pack()
        self.qty_e.insert(0, "10")
        self.qty_e.focus_set()
        self.qty_e.select_range(0, "end")

        ctk.CTkLabel(self, text="COST PRICE (optional)",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(pady=(10, 4))
        self.cost_e = ctk.CTkEntry(self, width=220, height=36,
                                   corner_radius=8, font=font(13),
                                   fg_color=BG_INPUT, border_color=BORDER,
                                   border_width=1, justify="center",
                                   placeholder_text="leave blank to use current")
        self.cost_e.pack()

        ctk.CTkLabel(self, text="EXPIRATION DATE  (optional, YYYY-MM-DD)",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(pady=(10, 4))
        self.exp_e = ctk.CTkEntry(self, width=220, height=36,
                                  corner_radius=8, font=font(13),
                                  fg_color=BG_INPUT, border_color=BORDER,
                                  border_width=1, justify="center",
                                  placeholder_text="leave blank if none")
        self.exp_e.pack()

        ctk.CTkButton(self, text="Restock",
                      width=220, height=38, corner_radius=8,
                      font=font_bold(12),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._save).pack(pady=(16, 14))

    def _save(self):
        try:
            qty = int(self.qty_e.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter a valid positive number.")
            return

        cost_raw = self.cost_e.get().strip()
        cost = None
        if cost_raw:
            try:
                cost = float(cost_raw)
                if cost < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Cost must be a non-negative number.")
                return

        exp_date = self.exp_e.get().strip() or None
        if exp_date:
            try:
                datetime.strptime(exp_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Expiration date must be in YYYY-MM-DD format."
                )
                return

        ok, msg = InventoryController.restock(
            self.user, self.product["product_id"],
            quantity=qty,
            cost_price=cost,
            expiration_date=exp_date,
        )
        if ok:
            messagebox.showinfo("Restocked", msg)
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


# ─────────────────────────────────────────────
# BATCHES DIALOG
# ─────────────────────────────────────────────

class BatchesDialog(ctk.CTkToplevel):

    def __init__(self, parent, user, product, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.product = product
        self.on_save = on_save
        self.title(f"Batches — {product['name']}")
        self.geometry("720x500")
        self.resizable(True, True)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        p = self.product

        ctk.CTkLabel(self, text=f"Batches — {p['name']}",
                     font=font_bold(15),
                     text_color=FG_PRIMARY).pack(pady=(14, 2))

        ctk.CTkLabel(self, text=f"{p['product_code']}  •  {p['supplier_name'] or '-'}",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(pady=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=BG_CARD,
                                                 corner_radius=10,
                                                 border_width=1,
                                                 border_color=BORDER)
        self.list_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self._render()

    def _render(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        batches = InventoryController.list_batches(self.product["product_id"])
        if not batches:
            ctk.CTkLabel(self.list_frame,
                         text="No batches.",
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=20)
            return

        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))
        for text, width in [("Batch No", 170), ("Qty", 55),
                            ("Cost", 75), ("Expires", 105), ("Received", 130)]:
            ctk.CTkLabel(header, text=text, width=width, anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

        today = datetime.now().date()

        for i, b in enumerate(batches):
            bg = BG_ROW_ALT if i % 2 else BG_CARD
            row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=b["batch_no"] or "-",
                         width=170, anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=4, pady=6)

            qty_color = FG_PRIMARY if b["quantity"] > 0 else FG_MUTED
            ctk.CTkLabel(row, text=str(b["quantity"]),
                         width=55, anchor="w",
                         font=font_bold(11),
                         text_color=qty_color).pack(side="left", padx=4)

            ctk.CTkLabel(row, text=f"₱{b['cost_price']:.2f}",
                         width=75, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

            exp_text = b["expiration_date"] or "—"
            exp_color = FG_MUTED
            if b["expiration_date"]:
                try:
                    exp = datetime.strptime(b["expiration_date"], "%Y-%m-%d").date()
                    days = (exp - today).days
                    if days < 0:
                        exp_color = DANGER
                    elif days <= 30:
                        exp_color = "#D97706"
                    else:
                        exp_color = FG_SECONDARY
                except ValueError:
                    pass

            ctk.CTkLabel(row, text=exp_text,
                         width=105, anchor="w",
                         font=font(11),
                         text_color=exp_color).pack(side="left", padx=4)

            ctk.CTkLabel(row, text=(b["received_at"] or "")[:10],
                         width=130, anchor="w",
                         font=font(10),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

            # ---- Edit + Discard buttons ----
            ctk.CTkButton(row, text="Edit", width=60, height=26,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=ACCENT, hover_color=ACCENT_HOVER,
                          command=lambda bt=b: self._edit(bt)
                          ).pack(side="right", padx=(0, 4))

            if b["quantity"] > 0:
                ctk.CTkButton(row, text="Discard", width=70, height=26,
                              corner_radius=6,
                              font=font_bold(11),
                              fg_color=DANGER, hover_color=DANGER_HOVER,
                              command=lambda bid=b["batch_id"], bn=b["batch_no"]:
                                  self._discard(bid, bn)
                              ).pack(side="right", padx=(0, 4))

    def _discard(self, batch_id, batch_no):
        if not messagebox.askyesno(
            "Discard Batch",
            f"Set quantity of {batch_no} to 0?\n\n"
            "Use this when the stock is physically thrown away."
        ):
            return

        ok, msg = InventoryController.discard_batch(self.user, batch_id)
        if ok:
            self._render()
            self.on_save()
        else:
            messagebox.showerror("Error", msg)

    def _edit(self, batch):
        EditBatchDialog(self, self.user, batch, on_save=self._after_edit)

    def _after_edit(self):
        self._render()
        self.on_save()


# ─────────────────────────────────────────────
# EDIT BATCH DIALOG
# ─────────────────────────────────────────────

class EditBatchDialog(ctk.CTkToplevel):

    def __init__(self, parent, user, batch, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.batch = batch
        self.on_save = on_save

        self.title(f"Edit {batch['batch_no']}")
        self.geometry("380x460")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        b = self.batch

        ctk.CTkLabel(self, text="Edit Batch",
                     font=font_bold(15),
                     text_color=FG_PRIMARY).pack(pady=(16, 2))

        ctk.CTkLabel(self, text=b["batch_no"],
                     font=font(11),
                     text_color=FG_SECONDARY).pack(pady=(0, 12))

        card = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=10,
                            border_width=1,
                            border_color=BORDER)
        card.pack(fill="x", padx=20, pady=(0, 10))

        # ---- Quantity ----
        ctk.CTkLabel(card, text="QUANTITY", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=14, pady=(14, 4))
        self.qty_e = ctk.CTkEntry(card, height=32, corner_radius=6,
                                  font=font(12), fg_color=BG_INPUT,
                                  border_color=BORDER, border_width=1)
        self.qty_e.pack(fill="x", padx=14)
        self.qty_e.insert(0, str(b["quantity"]))

        # ---- Cost price ----
        ctk.CTkLabel(card, text="COST PRICE (₱)", anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=14, pady=(10, 4))
        self.cost_e = ctk.CTkEntry(card, height=32, corner_radius=6,
                                   font=font(12), fg_color=BG_INPUT,
                                   border_color=BORDER, border_width=1)
        self.cost_e.pack(fill="x", padx=14)
        self.cost_e.insert(0, str(b["cost_price"] or 0))

        # ---- Expiration date ----
        ctk.CTkLabel(card, text="EXPIRATION DATE  (YYYY-MM-DD, blank = none)",
                     anchor="w",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(fill="x", padx=14, pady=(10, 4))
        self.exp_e = ctk.CTkEntry(card, height=32, corner_radius=6,
                                  font=font(12), fg_color=BG_INPUT,
                                  border_color=BORDER, border_width=1,
                                  placeholder_text="YYYY-MM-DD")
        self.exp_e.pack(fill="x", padx=14, pady=(0, 14))
        if b["expiration_date"]:
            self.exp_e.insert(0, b["expiration_date"])

        # ---- Buttons ----
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(6, 16))

        ctk.CTkButton(btn_row, text="Cancel", width=100, height=36,
                      corner_radius=8, font=font_bold(12),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self.destroy).pack(side="left", padx=6)

        ctk.CTkButton(btn_row, text="Save", width=140, height=36,
                      corner_radius=8, font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._save).pack(side="left", padx=6)

    def _save(self):
        try:
            qty = int(self.qty_e.get())
            if qty < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a non-negative integer.")
            return

        try:
            cost = float(self.cost_e.get() or 0)
            if cost < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Cost must be a non-negative number.")
            return

        exp_raw = self.exp_e.get().strip()
        if exp_raw:
            try:
                datetime.strptime(exp_raw, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Expiration date must be in YYYY-MM-DD format."
                )
                return
            expiration = exp_raw
        else:
            expiration = None

        ok, msg = InventoryController.update_batch(
            self.user,
            self.batch["batch_id"],
            quantity=qty,
            cost_price=cost,
            expiration_date=expiration,
        )
        if ok:
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


# ─────────────────────────────────────────────
# CATEGORY DIALOG
# ─────────────────────────────────────────────

class CategoryDialog(ctk.CTkToplevel):

    def __init__(self, parent, user, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.on_save = on_save
        self.title("Manage Categories")
        self.geometry("480x460")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

    def _build(self):
        ctk.CTkLabel(self, text="Manage Categories",
                     font=font_bold(15),
                     text_color=FG_PRIMARY).pack(pady=(14, 4))

        card = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=10,
                            border_width=1, border_color=BORDER)
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

        cats = InventoryController.list_categories()
        if not cats:
            ctk.CTkLabel(self.list_frame, text="No categories yet.",
                         font=font(12), text_color=FG_MUTED).pack(pady=20)
            return

        for c in cats:
            row = ctk.CTkFrame(self.list_frame, fg_color=BG_ROW_ALT,
                               corner_radius=6)
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

        ok, msg = InventoryController.add_category(self.user, name, desc)
        if not ok:
            messagebox.showerror("Error", msg)
            return

        self.name_e.delete(0, "end")
        self.desc_e.delete(0, "end")
        self._load_categories()
        self.on_save()