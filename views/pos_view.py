# ─────────────────────────────────────────────
# POS VIEW (softened 3F MiniMart branding + search + pictures)
# ─────────────────────────────────────────────

import os
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox

from controllers.transaction_controller import TransactionController
from controllers.pos_controller import POSController
from controllers.inventory_controller import InventoryController
from utils import prepare_dialog_screen
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BG_INPUT, BG_ROW_ALT, BORDER,
    FG_PRIMARY, FG_SECONDARY, FG_MUTED,
    BRAND_GREEN, BRAND_YELLOW,
    ACCENT, ACCENT_HOVER, SUCCESS, DANGER, DANGER_HOVER,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


class POSView(ctk.CTkFrame):

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user
        self.controller = POSController()          # cart-only helper
        self.categories = InventoryController.list_categories()
        self.selected_category_id = None
        self.search_query = ""
        self.products = InventoryController.list_products()
        self._build()
        self._refresh_cart()

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

        ctk.CTkLabel(title_box, text="POS",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="Select products and complete the sale",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ═════════════════════════════════════════
        # TWO-COLUMN LAYOUT
        # ═════════════════════════════════════════

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # ═════════════════════════════════════════
        # LEFT — PRODUCTS
        # ═════════════════════════════════════════

        left = ctk.CTkFrame(body, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # ---- Products title bar ----
        products_title = ctk.CTkFrame(left, fg_color="transparent")
        products_title.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(products_title, text="Products",
                     font=font_bold(15),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(side="left")

        self.count_label = ctk.CTkLabel(products_title, text="",
                                        font=font_bold(11),
                                        text_color=FG_SECONDARY)
        self.count_label.pack(side="right")

        # ---- Row 1: search ----
        search_row = ctk.CTkFrame(left, fg_color="transparent")
        search_row.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(search_row, text="Search",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        self.search_e = ctk.CTkEntry(
            search_row,
            placeholder_text="Search by name or product code...",
            textvariable=self.search_var,
            height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
        )
        self.search_e.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(search_row, text="✕", width=36, height=36,
                      corner_radius=8,
                      font=font(13),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._clear_search).pack(side="left")

        # ---- Row 2: category filter ----
        filter_row = ctk.CTkFrame(left, fg_color="transparent")
        filter_row.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(filter_row, text="Category",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.category_names = ["All Categories"] + [c["name"] for c in self.categories]
        self.category_var = ctk.StringVar(value="All Categories")

        self.category_menu = ctk.CTkOptionMenu(
            filter_row,
            values=self.category_names,
            variable=self.category_var,
            width=200, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=NEUTRAL,
            text_color=FG_PRIMARY,
            command=self._on_category_change,
        )
        self.category_menu.pack(side="left")

        # ---- Product list ----
        self.product_frame = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.product_frame.pack(fill="both", expand=True, padx=10, pady=(0, 14))

        self._render_products()

        # ═════════════════════════════════════════
        # RIGHT — CART
        # ═════════════════════════════════════════

        right = ctk.CTkFrame(body, width=400, fg_color=BG_CARD,
                             corner_radius=12,
                             border_width=1,
                             border_color=BORDER)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # ---- Cart title ----
        ctk.CTkLabel(right, text="Cart",
                     font=font_bold(15),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x", padx=16, pady=(14, 6))

        # ---- Cart list ----
        self.cart_frame = ctk.CTkScrollableFrame(right, fg_color="transparent",
                                                 height=200)
        self.cart_frame.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # ---- Divider ----
        ctk.CTkFrame(right, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(4, 0))

        # ---- Total ----
        total_box = ctk.CTkFrame(right, fg_color="transparent")
        total_box.pack(fill="x", padx=16, pady=(10, 6))

        ctk.CTkLabel(total_box, text="Total",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left")

        self.total_label = ctk.CTkLabel(total_box, text="₱0.00",
                                        font=font_bold(20),
                                        text_color=ACCENT)
        self.total_label.pack(side="right")

        # ---- Payment method ----
        ctk.CTkLabel(right, text="PAYMENT METHOD",
                     font=font_bold(10),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", padx=16, pady=(6, 4))

        self.payment_var = ctk.StringVar(value="Cash")
        self.payment_menu = ctk.CTkOptionMenu(
            right,
            values=["Cash", "GCash"],
            variable=self.payment_var,
            height=38,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=NEUTRAL,
            text_color=FG_PRIMARY,
        )
        self.payment_menu.pack(fill="x", padx=16, pady=(0, 8))

        # ---- GCash reference (created here, packed later when GCash picked) ----
        self.ref_label = ctk.CTkLabel(right, text="GCASH REFERENCE NO.",
                                      font=font_bold(10),
                                      text_color=FG_SECONDARY,
                                      anchor="w")
        self.ref_entry = ctk.CTkEntry(
            right,
            height=38,
            corner_radius=8,
            font=font(13),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
            placeholder_text="e.g. 1234567890123",
        )

        # ---- Amount paid ----
        self.amount_label = ctk.CTkLabel(right, text="AMOUNT PAID",
                                         font=font_bold(10),
                                         text_color=FG_SECONDARY,
                                         anchor="w")
        self.amount_label.pack(fill="x", padx=16, pady=(0, 4))

        self.amount_entry = ctk.CTkEntry(
            right,
            height=38,
            corner_radius=8,
            font=font(13),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
            placeholder_text="0.00",
        )
        self.amount_entry.pack(fill="x", padx=16, pady=(0, 12))

        # ---- Attach the toggle AFTER widgets are created ----
        self.payment_var.trace_add("write", self._on_payment_method_change)

        # ---- Buttons ----
        ctk.CTkButton(
            right, text="Checkout",
            height=44, corner_radius=8,
            font=font_bold(14),
            fg_color=BRAND_GREEN, hover_color="#1E9040",
            command=self._checkout,
        ).pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkButton(
            right, text="Clear Cart",
            height=38, corner_radius=8,
            font=font_bold(12),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._clear,
        ).pack(fill="x", padx=16, pady=(0, 14))

    # ─────────────────────────────────────────────
    # PAYMENT METHOD CHANGE (show/hide GCash reference)
    # ─────────────────────────────────────────────

    def _on_payment_method_change(self, *args):
        """Show or hide the GCash reference field based on payment method."""
        method = self.payment_var.get()

        if method == "GCash":
            # ---- Insert ABOVE the Amount Paid label ----
            self.ref_label.pack(fill="x", padx=16, pady=(0, 4),
                                before=self.amount_label)
            self.ref_entry.pack(fill="x", padx=16, pady=(0, 12),
                                before=self.amount_label)
        else:
            self.ref_label.pack_forget()
            self.ref_entry.pack_forget()
            self.ref_entry.delete(0, "end")

    # ─────────────────────────────────────────────
    # SEARCH
    # ─────────────────────────────────────────────

    def _on_search_change(self, *args):
        self.search_query = self.search_var.get().strip().lower()
        self._render_products()

    def _clear_search(self):
        self.search_var.set("")

    def _matches_search(self, p):
        """Match against product name or code."""
        q = self.search_query
        fields = [
            (p["name"] or "").lower(),
            (p["product_code"] or "").lower(),
        ]
        return any(q in f for f in fields)

    # ─────────────────────────────────────────────
    # CATEGORY FILTER
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

        self.products = InventoryController.list_by_category(self.selected_category_id)
        self._render_products()

    # ─────────────────────────────────────────────
    # CART HELPERS
    # ─────────────────────────────────────────────

    def _get_cart_quantity(self, product_id):
        """Return how many of this product are currently in the cart."""
        for item in self.controller.cart:
            if item["product_id"] == product_id:
                return item["quantity"]
        return 0

    # ─────────────────────────────────────────────
    # PRODUCT RENDERING
    # ─────────────────────────────────────────────

    def _render_products(self):
        for w in self.product_frame.winfo_children():
            w.destroy()

        # ---- Apply search filter ----
        products = self.products
        if self.search_query:
            products = [p for p in products if self._matches_search(p)]

        # ---- Update count ----
        self.count_label.configure(text=f"{len(products)} product(s)")

        # ---- Empty state ----
        if not products:
            msg = "No products match your search." if self.search_query \
                  else "No products in this category."
            ctk.CTkLabel(self.product_frame,
                         text=msg,
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            return

        # ---- Render each product ----
        for p in products:
            self._render_product_row(p)

    def _render_product_row(self, product):
        """Render a product as a fully clickable card."""
        stock = product["stock_qty"]
        out_of_stock = stock <= 0

        # ---- Safe read of low_stock_level (sqlite3.Row has no .get()) ----
        low_level = product["low_stock_level"]
        if low_level is None:
            low_level = 10

        # ---- How many are already in the cart? ----
        in_cart = self._get_cart_quantity(product["product_id"])
        at_max = (stock > 0 and in_cart >= stock)

        # ---- Card colors ----
        card_fg = BG_INPUT if (out_of_stock or at_max) else BG_CARD
        hover_fg = NEUTRAL if (out_of_stock or at_max) else "#EAF0FF"

        # ═════════════════════════════════════════
        # Card (plain frame, all children get bound)
        # ═════════════════════════════════════════
        card = ctk.CTkFrame(
            self.product_frame,
            fg_color=card_fg,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            height=76,
        )
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)

        # ─────────────────────────────────────
        # Thumbnail
        # ─────────────────────────────────────
        thumb = self._load_thumbnail(product["image_path"], size=(56, 56))

        thumb_box = ctk.CTkFrame(
            card,
            width=56, height=56,
            fg_color=NEUTRAL if (out_of_stock or at_max) else "#F1F5F9",
            corner_radius=8,
        )
        thumb_box.place(x=10, rely=0.5, anchor="w")
        thumb_box.pack_propagate(False)

        if thumb:
            thumb_label = ctk.CTkLabel(thumb_box, image=thumb, text="")
            thumb_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            thumb_label = ctk.CTkLabel(
                thumb_box,
                text="📦",
                font=font(22),
                text_color=FG_MUTED if (out_of_stock or at_max) else FG_SECONDARY,
            )
            thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        # ─────────────────────────────────────
        # Info block: name + meta row
        # ─────────────────────────────────────
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.place(x=78, rely=0.5, anchor="w")

        name_label = ctk.CTkLabel(
            info,
            text=product["name"],
            font=font_bold(13),
            text_color=FG_MUTED if (out_of_stock or at_max) else FG_PRIMARY,
            anchor="w",
        )
        name_label.pack(anchor="w")

        meta = ctk.CTkFrame(info, fg_color="transparent")
        meta.pack(anchor="w", pady=(2, 0))

        code_label = ctk.CTkLabel(meta, text=product["product_code"] or "-",
                                  font=font(10), text_color=FG_MUTED)
        code_label.pack(side="left")

        sep1 = ctk.CTkLabel(meta, text="  •  ", font=font(10),
                            text_color=FG_MUTED)
        sep1.pack(side="left")

        price_label = ctk.CTkLabel(
            meta,
            text=f"₱{product['price']:.2f}",
            font=font_bold(12),
            text_color=FG_MUTED if (out_of_stock or at_max) else ACCENT,
        )
        price_label.pack(side="left")

        sep2 = ctk.CTkLabel(meta, text="  •  ", font=font(10),
                            text_color=FG_MUTED)
        sep2.pack(side="left")

        # ---- Stock chip ----
        if out_of_stock:
            stock_text = "Out of Stock"
            stock_color = DANGER
        elif at_max:
            stock_text = f"Max in cart ({in_cart}/{stock})"
            stock_color = "#D97706"     # amber
        elif stock <= low_level:
            stock_text = f"Low: {stock}"
            stock_color = "#D97706"
        else:
            stock_text = f"Stock: {stock}"
            stock_color = SUCCESS

        stock_label = ctk.CTkLabel(meta, text=stock_text,
                                   font=font_bold(10),
                                   text_color=stock_color)
        stock_label.pack(side="left")

        # ═════════════════════════════════════════
        # Bind click + hover to EVERY child of the card
        # ═════════════════════════════════════════
        if out_of_stock:
            click_action = lambda: messagebox.showwarning(
                "Out of Stock",
                f"{product['name']} is out of stock."
            )
        elif at_max:
            click_action = lambda: messagebox.showwarning(
                "Insufficient Stock",
                f"Cannot add more of {product['name']}.\n\n"
                f"Stock available: {stock}\n"
                f"Already in cart: {in_cart}\n\n"
                f"You've reached the maximum available quantity."
            )
        else:
            click_action = lambda prod=product: self._add_to_cart(prod)

        widgets = [
            card,
            thumb_box, thumb_label,
            info, name_label,
            meta, code_label, sep1, price_label, sep2, stock_label,
        ]

        for w in widgets:
            # ---- Click ----
            w.bind("<Button-1>", lambda e, action=click_action: action())

            # ---- Hover in ----
            w.bind("<Enter>", lambda e, c=card, h=hover_fg:
                   c.configure(fg_color=h))

            # ---- Hover out ----
            w.bind("<Leave>", lambda e, c=card, f=card_fg:
                   c.configure(fg_color=f))

            # ---- Hand cursor ----
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass

    # ─────────────────────────────────────────────
    # THUMBNAIL LOADER
    # ─────────────────────────────────────────────

    def _load_thumbnail(self, image_path, size=(56, 56)):
        """Load + resize a product image into a CTkImage."""
        if not image_path or not os.path.exists(image_path):
            return None
        try:
            img = Image.open(image_path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception:
            return None

    # ─────────────────────────────────────────────
    # CART
    # ─────────────────────────────────────────────

    def _add_to_cart(self, product):
        stock = product["stock_qty"]

        # ---- Already out of stock (safety net) ----
        if stock <= 0:
            messagebox.showwarning(
                "Out of Stock",
                f"{product['name']} is out of stock."
            )
            return

        # ---- How many are already in the cart? ----
        existing = self._get_cart_quantity(product["product_id"])

        # ---- Would adding one more exceed the stock? ----
        if existing + 1 > stock:
            messagebox.showwarning(
                "Insufficient Stock",
                f"Cannot add more of {product['name']}.\n\n"
                f"Stock available: {stock}\n"
                f"Already in cart: {existing}\n\n"
                f"You've reached the maximum available quantity."
            )
            return

        # ---- Safe to add ----
        self.controller.add_to_cart(product)
        self._refresh_cart()

    def _remove(self, product_id):
        self.controller.remove_from_cart(product_id)
        self._refresh_cart()

    def _decrease(self, product_id):
        """Reduce the quantity of a cart item by 1 (removes it if it hits 0)."""
        self.controller.decrease_quantity(product_id)
        self._refresh_cart()

    def _clear(self):
        self.controller.clear_cart()
        self._refresh_cart()

    def _refresh_cart(self):
        for w in self.cart_frame.winfo_children():
            w.destroy()

        if not self.controller.cart:
            ctk.CTkLabel(self.cart_frame,
                         text="Cart is empty",
                         font=font(11),
                         text_color=FG_MUTED).pack(pady=30)
            self.total_label.configure(text="₱0.00")
            # ---- Keep product cards in sync ----
            self._render_products()
            return

        for i, item in enumerate(self.controller.cart):
            bg = BG_ROW_ALT if i % 2 else "transparent"

            row = ctk.CTkFrame(self.cart_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            # ---- Item name ----
            ctk.CTkLabel(row, text=item['name'],
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=(8, 4), pady=6)

            # ---- Quantity ----
            ctk.CTkLabel(row, text=f"×{item['quantity']}",
                         width=32,
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=4)

            # ---- Subtotal ----
            ctk.CTkLabel(row, text=f"₱{item['price'] * item['quantity']:.2f}",
                         font=font_bold(11),
                         text_color=ACCENT).pack(side="right", padx=(4, 8))

            # ---- Remove (✕) button ----
            ctk.CTkButton(row, text="✕", width=30, height=28,
                          corner_radius=6,
                          font=font(12),
                          fg_color=DANGER, hover_color=DANGER_HOVER,
                          command=lambda pid=item["product_id"]: self._remove(pid)
                          ).pack(side="right", padx=3, pady=4)

            # ---- Minus (-) button ----
            ctk.CTkButton(row, text="-", width=30, height=28,
                          corner_radius=6,
                          font=font_bold(16),
                          fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                          text_color=NEUTRAL_TEXT,
                          command=lambda pid=item["product_id"]: self._decrease(pid)
                          ).pack(side="right", padx=3, pady=4)

        self.total_label.configure(text=f"₱{self.controller.get_total():.2f}")

        # ---- Keep product cards in sync with cart state ----
        self._render_products()

    # ─────────────────────────────────────────────
    # CHECKOUT (with confirmation dialog)
    # ─────────────────────────────────────────────

    def _checkout(self):
        if not self.controller.cart:
            messagebox.showwarning("Empty Cart", "Add products before checking out.")
            return

        # ═════════════════════════════════════════
        # Re-validate stock for every cart item
        # (guards against stock changing mid-sale)
        # ═════════════════════════════════════════
        fresh_products = {
            p["product_id"]: p for p in InventoryController.list_products()
        }
        problems = []
        for item in self.controller.cart:
            fresh = fresh_products.get(item["product_id"])
            if fresh is None:
                problems.append(f"• {item['name']}: product not found.")
            elif item["quantity"] > fresh["stock_qty"]:
                problems.append(
                    f"• {item['name']}: you have {item['quantity']} in cart "
                    f"but only {fresh['stock_qty']} in stock."
                )

        if problems:
            messagebox.showerror(
                "Stock Changed",
                "Some items in your cart exceed available stock:\n\n" +
                "\n".join(problems) +
                "\n\nPlease adjust the cart before checking out."
            )
            self.products = InventoryController.list_by_category(
                self.selected_category_id
            )
            self._render_products()
            return

        # ═════════════════════════════════════════
        # Payment handling
        # ═════════════════════════════════════════
        method = self.payment_var.get()
        gcash_reference = None

        if method == "GCash":
            paid = self.controller.get_total()

            # ---- Require the GCash reference number ----
            gcash_reference = self.ref_entry.get().strip()
            if not gcash_reference:
                messagebox.showerror(
                    "Missing Reference",
                    "Please enter the GCash reference number."
                )
                self.ref_entry.focus_set()
                return
        else:
            try:
                paid = float(self.amount_entry.get() or 0)
            except ValueError:
                messagebox.showerror("Error", "Invalid amount.")
                return

            total = self.controller.get_total()
            if paid < total:
                messagebox.showerror(
                    "Insufficient Payment",
                    f"Amount paid (₱{paid:.2f}) is less than the total (₱{total:.2f})."
                )
                return

        total = self.controller.get_total()
        change = paid - total if method == "Cash" else 0

        confirm = CheckoutConfirmDialog(
            self.winfo_toplevel(),
            total=total,
            amount_paid=paid,
            payment_method=method,
            change=change,
            gcash_reference=gcash_reference,
        )

        if not confirm.confirmed:
            return

        # ═════════════════════════════════════════
        # Use TransactionController to persist
        # ═════════════════════════════════════════
        ok, result, change = TransactionController.create(
            user_id=self.user["user_id"],
            cart=self.controller.cart,
            payment_method=method,
            amount_paid=paid,
            gcash_reference=gcash_reference,
        )
        if not ok:
            messagebox.showerror("Checkout Failed", str(result))
            return

        messagebox.showinfo(
            "Success",
            f"Transaction #{result} completed.\n"
            f"Total: ₱{total:.2f}\n"
            f"Paid: ₱{paid:.2f}\n"
            f"Change: ₱{change:.2f}"
        )

        # ---- Clear the cart + reset UI ----
        self.controller.clear_cart()
        self.amount_entry.delete(0, "end")
        self.ref_entry.delete(0, "end")

        self.products = InventoryController.list_by_category(self.selected_category_id)
        self._render_products()
        self._refresh_cart()


# ─────────────────────────────────────────────
# CHECKOUT CONFIRMATION DIALOG (styled)
# ─────────────────────────────────────────────

class CheckoutConfirmDialog(ctk.CTkToplevel):

    def __init__(self, parent, total, amount_paid, payment_method, change,
                 gcash_reference=None):
        super().__init__(parent)
        self.parent = parent
        self.total = total
        self.amount_paid = amount_paid
        self.payment_method = payment_method
        self.change = change
        self.gcash_reference = gcash_reference

        self.confirmed = False

        self.title("Confirm Checkout")
        self.geometry("440x400")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

        self.transient(parent)
        self.grab_set()
        self.focus_force()
        self.wait_window(self)

    def _build(self):
        ctk.CTkLabel(self, text="Confirm Checkout",
                     font=font_bold(18),
                     text_color=FG_PRIMARY).pack(pady=(20, 4))

        ctk.CTkLabel(self, text="Please review the transaction before confirming",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(pady=(0, 14))

        card = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER)
        card.pack(fill="x", padx=24, pady=(0, 10))

        rows = [
            ("Total",           f"₱{self.total:.2f}",        ACCENT),
            ("Payment Method",  self.payment_method,         FG_PRIMARY),
        ]
        if self.payment_method == "GCash" and self.gcash_reference:
            rows.append(("GCash Reference", self.gcash_reference, FG_PRIMARY))
        rows += [
            ("Amount Paid",     f"₱{self.amount_paid:.2f}", FG_PRIMARY),
            ("Change",          f"₱{self.change:.2f}",       BRAND_GREEN),
        ]
        for i, (label, value, color) in enumerate(rows):
            if i > 0:
                ctk.CTkFrame(card, height=1, fg_color=BORDER).pack(
                    fill="x", padx=14)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=10)

            ctk.CTkLabel(row, text=label,
                         font=font_bold(11),
                         text_color=FG_SECONDARY,
                         anchor="w").pack(side="left")

            ctk.CTkLabel(row, text=value, anchor="e",
                         font=font_bold(13),
                         text_color=color).pack(side="right")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=20)

        ctk.CTkButton(btn_row, text="Cancel", width=140, height=42,
                      corner_radius=8,
                      font=font_bold(13),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._cancel).pack(side="left", padx=6)

        ctk.CTkButton(btn_row, text="Confirm", width=160, height=42,
                      corner_radius=8,
                      font=font_bold(13),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._confirm).pack(side="left", padx=6)

    def _confirm(self):
        self.confirmed = True
        self.destroy()

    def _cancel(self):
        self.confirmed = False
        self.destroy()