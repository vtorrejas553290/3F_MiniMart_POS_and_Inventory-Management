# ─────────────────────────────────────────────
# RECEIPT DIALOG
# ─────────────────────────────────────────────

import os
import sys
import subprocess
import customtkinter as ctk
from tkinter import messagebox

from utils import prepare_dialog_screen
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BORDER,
    FG_PRIMARY, FG_SECONDARY,
    BRAND_GREEN,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


# ─────────────────────────────────────────────
# RECEIPTS FOLDER
# ─────────────────────────────────────────────

RECEIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "receipts")
RECEIPTS_DIR = os.path.abspath(RECEIPTS_DIR)
os.makedirs(RECEIPTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# RECEIPT DIALOG
# ─────────────────────────────────────────────

class ReceiptDialog(ctk.CTkToplevel):

    WIDTH = 42
    MONO_FONT = ("Consolas", 12)

    def __init__(self, parent, txn_id, user, cart,
                 payment_method, amount_paid, change, total,
                 gcash_reference=None, created_at=None):
        super().__init__(parent)
        self.parent = parent
        self.txn_id = txn_id
        self.user = user
        self.cart = cart
        self.payment_method = payment_method
        self.amount_paid = amount_paid
        self.change = change
        self.total = total
        self.gcash_reference = gcash_reference
        self.created_at = created_at

        self.title(f"Receipt #{txn_id}")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)

        self._build()

        # Set final size AFTER widgets are built so winfo_reqheight is accurate
        self.update_idletasks()
        self._fit_to_content()

        prepare_dialog_screen(self, self.parent)

        self.transient(parent)
        self.grab_set()
        self.focus_force()

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        # ---- Header ----
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(header, text="Receipt",
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

        ctk.CTkLabel(self,
                     text=f"Transaction #{self.txn_id} completed",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", padx=16, pady=(0, 8))

        # ---- Receipt body ----
        card = ctk.CTkFrame(self, fg_color="#FFFFFF",
                            corner_radius=8,
                            border_width=1,
                            border_color=BORDER)
        card.pack(padx=16, pady=(0, 10))   # no expand — let it shrink to fit

        receipt_text = self._render_receipt_text()

        self.receipt_label = ctk.CTkLabel(
            card,
            text=receipt_text,
            font=self.MONO_FONT,
            text_color="#000000",
            justify="left",
            anchor="nw",
        )
        self.receipt_label.pack(padx=14, pady=14)

        # ---- Buttons ----
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(btn_row, text="Close",
                      width=120, height=40,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self.destroy
                      ).pack(side="left")

        ctk.CTkButton(btn_row, text="Open in Notepad",
                      height=40,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._open_in_editor
                      ).pack(side="right", fill="x", expand=True, padx=(8, 0))

    # ─────────────────────────────────────────────
    # AUTO-SIZE — snug fit
    # ─────────────────────────────────────────────

    def _fit_to_content(self):
        """
        Measure the top-level's natural content size and set the window
        to exactly that. Since we removed `expand=True` on the card and
        button row, winfo_reqheight() now reflects the true content size.
        """
        self.update_idletasks()

        # Total content width/height required by the window
        req_w = self.winfo_reqwidth()
        req_h = self.winfo_reqheight()

        # Small safety margin so scrollbars/borders don't clip
        window_w = req_w + 8
        window_h = req_h + 8

        # Ensure a reasonable minimum
        window_w = max(window_w, 520)
        window_h = max(window_h, 380)

        self.geometry(f"{window_w}x{window_h}")
        self.minsize(window_w, window_h)

    # ─────────────────────────────────────────────
    # RECEIPT TEXT BUILDER
    # ─────────────────────────────────────────────

    def _render_receipt_text(self):
        w = self.WIDTH
        lines = []

        def center(text):
            return text.center(w)

        def divider():
            return "=" * w

        def thin_divider():
            return "-" * w

        # ---- Header ----
        lines.append(divider())
        lines.append(center("3F MiniMart"))
        lines.append(divider())

        # ---- Meta ----
        lines.append(f"Receipt #: {self.txn_id}".ljust(w))
        if self.created_at:
            lines.append(f"Date     : {self.created_at}".ljust(w))
        cashier = (self.user.get("full_name")
                   or self.user.get("username")
                   or "-")
        lines.append(f"Cashier  : {cashier}".ljust(w))
        lines.append(thin_divider())

        # ---- Items table ----
        lines.append(
            "ITEM".ljust(20)
            + "QTY".rjust(5)
            + "PRICE".rjust(9)
            + "TOTAL".rjust(8)
        )
        lines.append(thin_divider())

        for item in self.cart:
            name = item["name"]
            if item.get("brand"):
                name = f"{item['brand']} {name}"
            if item.get("size"):
                name = f"{name} {item['size']}"

            qty = item["quantity"]
            price = item["price"]
            subtotal = price * qty

            display = name[:20] if len(name) > 20 else name
            rest = name[20:] if len(name) > 20 else ""

            lines.append(
                display.ljust(20)
                + f"{qty}".rjust(5)
                + f"₱{price:.2f}".rjust(9)
                + f"₱{subtotal:.2f}".rjust(8)
            )

            if rest:
                lines.append(("    " + rest).ljust(w))

        lines.append(thin_divider())

        # ---- Totals ----
        lines.append("Subtotal:".ljust(28) + f"₱{self.total:.2f}".rjust(14))
        lines.append(f"Payment: {self.payment_method}".ljust(w))

        if self.payment_method == "GCash" and self.gcash_reference:
            lines.append(f"GCash Ref: {self.gcash_reference}".ljust(w))

        lines.append("Amount Paid:".ljust(28) + f"₱{self.amount_paid:.2f}".rjust(14))
        lines.append("Change:".ljust(28) + f"₱{self.change:.2f}".rjust(14))

        lines.append(divider())
        lines.append(center("Thank you for your purchase!"))
        lines.append(center("Please come again"))
        lines.append(divider())

        return "\n".join(lines)

    # ─────────────────────────────────────────────
    # OPEN IN EDITOR
    # ─────────────────────────────────────────────

    def _open_in_editor(self):
        text = self._render_receipt_text()
        filename = f"receipt_{self.txn_id:06d}.txt"
        path = os.path.join(RECEIPTS_DIR, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save receipt:\n{e}")
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error",
                                 f"Could not open editor:\n{e}\n\n"
                                 f"File saved at:\n{path}")