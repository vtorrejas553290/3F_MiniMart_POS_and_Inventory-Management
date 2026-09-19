# ─────────────────────────────────────────────
# PURCHASE RECORDS VIEW (softened 3F MiniMart branding)
# ─────────────────────────────────────────────

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta

from controllers.purchase_controller import PurchaseController
from controllers.supplier_controller import SupplierController
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


# ─────────────────────────────────────────────
# PURCHASE RECORDS VIEW
# ─────────────────────────────────────────────

class PurchaseView(ctk.CTkFrame):

    # ─────────────────────────────────────────────
    # BUTTON COLORS
    # ─────────────────────────────────────────────

    ACTIVE_COLOR = ACCENT          # ---- soft blue when active ----
    IDLE_COLOR   = NEUTRAL         # ---- gray when idle ----

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG_MAIN)
        self.user = user
        self.filter_status = "All"
        self.search_query = ""
        self.date_from = ""
        self.date_to = ""

        # ---- Active quick-range button ----
        self.active_range_button = None
        self._programmatic_set = False

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

        ctk.CTkLabel(title_box, text="Purchase Records",
                     font=font_bold(22),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_box,
                     text="Track purchase orders and received stock",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", pady=(2, 0))

        # ---- Primary action ----
        ctk.CTkButton(header_frame, text="+ New Purchase Order",
                      height=38, corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._new_po_dialog).pack(side="right")

        # ═════════════════════════════════════════
        # FILTER CARD
        # ═════════════════════════════════════════

        filter_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                   corner_radius=12,
                                   border_width=1,
                                   border_color=BORDER)
        filter_card.pack(fill="x", padx=20, pady=(0, 10))

        # ---- Row 1: search + status + refresh ----
        row1 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(row1, text="Search",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        self.search_e = ctk.CTkEntry(
            row1,
            placeholder_text="Search by PO #, supplier, ordered by, notes...",
            textvariable=self.search_var,
            width=360, height=36,
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

        # ---- Status filter ----
        ctk.CTkLabel(row1, text="Status",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.status_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            row1,
            values=["All", "Ordered", "Received", "Cancelled"],
            variable=self.status_var,
            width=150, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=NEUTRAL,
            text_color=FG_PRIMARY,
            command=self._on_status_change,
        ).pack(side="left", padx=(0, 20))

        # ---- Refresh button ----
        ctk.CTkButton(row1, text="Refresh", width=100, height=36,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self._load).pack(side="right")

        # ---- Row 2: date range ----
        row2 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(row2, text="Date From",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.date_from_var = ctk.StringVar()
        self.date_from_var.trace_add("write", self._on_date_change)

        self.date_from_e = ctk.CTkEntry(
            row2, placeholder_text="YYYY-MM-DD",
            textvariable=self.date_from_var,
            width=130, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
        )
        self.date_from_e.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row2, text="Date To",
                     font=font_bold(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 8))

        self.date_to_var = ctk.StringVar()
        self.date_to_var.trace_add("write", self._on_date_change)

        self.date_to_e = ctk.CTkEntry(
            row2, placeholder_text="YYYY-MM-DD",
            textvariable=self.date_to_var,
            width=130, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            border_color=BORDER,
            border_width=1,
        )
        self.date_to_e.pack(side="left", padx=(0, 16))

        # ---- Quick range buttons ----
        self.btn_today = ctk.CTkButton(
            row2, text="Today", width=80, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._range_today,
        )
        self.btn_today.pack(side="left", padx=2)

        self.btn_7days = ctk.CTkButton(
            row2, text="Last 7 Days", width=100, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._range_7_days,
        )
        self.btn_7days.pack(side="left", padx=2)

        self.btn_month = ctk.CTkButton(
            row2, text="This Month", width=100, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._range_this_month,
        )
        self.btn_month.pack(side="left", padx=2)

        self.btn_clear = ctk.CTkButton(
            row2, text="Clear Dates", width=100, height=36,
            corner_radius=8,
            font=font(11),
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=NEUTRAL_TEXT,
            command=self._clear_dates,
        )
        self.btn_clear.pack(side="left", padx=2)

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

        self.list_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    # ─────────────────────────────────────────────
    # FILTERS — SEARCH
    # ─────────────────────────────────────────────

    def _on_search_change(self, *args):
        self.search_query = self.search_var.get().strip().lower()
        self._load()

    def _clear_search(self):
        self.search_var.set("")

    # ─────────────────────────────────────────────
    # FILTERS — STATUS
    # ─────────────────────────────────────────────

    def _on_status_change(self, choice):
        self.filter_status = choice
        self._load()

    # ─────────────────────────────────────────────
    # QUICK-RANGE BUTTON HIGHLIGHT
    # ─────────────────────────────────────────────

    def _highlight_button(self, button):
        # ---- Reset previous ----
        if self.active_range_button is not None:
            self.active_range_button.configure(
                fg_color=NEUTRAL, text_color=NEUTRAL_TEXT,
            )
        # ---- Highlight new ----
        if button is not None:
            button.configure(fg_color=ACCENT, text_color="#FFFFFF")
        self.active_range_button = button

    def _clear_button_highlight(self):
        if self.active_range_button is not None:
            self.active_range_button.configure(
                fg_color=NEUTRAL, text_color=NEUTRAL_TEXT,
            )
        self.active_range_button = None

    # ─────────────────────────────────────────────
    # FILTERS — DATE RANGE (auto-apply)
    # ─────────────────────────────────────────────

    def _on_date_change(self, *args):
        if self._programmatic_set:
            return

        d_from = self.date_from_var.get().strip()
        d_to = self.date_to_var.get().strip()

        if d_from and len(d_from) < 10:
            return
        if d_to and len(d_to) < 10:
            return
        if d_from and not self._is_valid_date(d_from):
            return
        if d_to and not self._is_valid_date(d_to):
            return
        if d_from and d_to and d_from > d_to:
            return

        self._clear_button_highlight()
        self.date_from = d_from
        self.date_to = d_to
        self._load()

    def _is_valid_date(self, text):
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    # ─────────────────────────────────────────────
    # QUICK RANGES
    # ─────────────────────────────────────────────

    def _range_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self._set_dates_programmatically(today, today, self.btn_today)

    def _range_7_days(self):
        today = datetime.now()
        start = (today - timedelta(days=6)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        self._set_dates_programmatically(start, end, self.btn_7days)

    def _range_this_month(self):
        today = datetime.now()
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        self._set_dates_programmatically(start, end, self.btn_month)

    def _clear_dates(self):
        self._set_dates_programmatically("", "", self.btn_clear)

    # ─────────────────────────────────────────────
    # HELPER — PROGRAMMATIC DATE SET
    # ─────────────────────────────────────────────

    def _set_dates_programmatically(self, d_from, d_to, button):
        self._programmatic_set = True
        self.date_from_var.set(d_from)
        self.date_to_var.set(d_to)
        self._programmatic_set = False

        self.date_from = d_from
        self.date_to = d_to
        self._highlight_button(button)
        self._load()

    # ─────────────────────────────────────────────
    # LOAD
    # ─────────────────────────────────────────────

    def _load(self):
        if self.filter_status == "All":
            purchases = PurchaseController.list_all()
        else:
            purchases = PurchaseController.list_by_status(self.filter_status)

        purchases = self._filter_by_date(purchases)

        if self.search_query:
            purchases = [p for p in purchases if self._matches_search(p)]

        self._render(purchases)

    def _filter_by_date(self, purchases):
        if not self.date_from and not self.date_to:
            return purchases

        result = []
        for p in purchases:
            created = (p["created_at"] or "")[:10]
            if self.date_from and created < self.date_from:
                continue
            if self.date_to and created > self.date_to:
                continue
            result.append(p)
        return result

    def _matches_search(self, p):
        q = self.search_query
        fields = [
            f"#{p['purchase_id']}",
            str(p["purchase_id"]),
            (p["supplier_name"] or "").lower(),
            (p["full_name"] or "").lower(),
            (p["username"] or "").lower(),
            (p["status"] or "").lower(),
            (p["notes"] or "").lower(),
        ]
        return any(q in f for f in fields)

    # ─────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────

    def _render(self, purchases):
        for w in self.list_frame.winfo_children():
            w.destroy()

        self.count_label.configure(text=f"{len(purchases)} record(s)")

        # ---- Header ----
        header = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))
        cols = [
            ("PO #",          70),
            ("Supplier",      170),
            ("Total",         90),
            ("Status",        100),
            ("Ordered By",    120),
            ("Date Ordered",  130),
            ("Date Received", 130),
        ]
        for text, width in cols:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

        # ---- Empty state ----
        if not purchases:
            ctk.CTkLabel(self.list_frame,
                         text="No records match your filters.",
                         font=font(12),
                         text_color=FG_MUTED).pack(pady=30)
            return

        # ---- Rows ----
        for i, p in enumerate(purchases):
            self._render_row(p, i)

    def _render_row(self, p, index=0):
        bg = BG_ROW_ALT if index % 2 else BG_CARD

        row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=6)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=f"#{p['purchase_id']}",
                     width=70, anchor="w",
                     font=font_bold(11),
                     text_color=ACCENT).pack(side="left", padx=3, pady=6)

        ctk.CTkLabel(row, text=p["supplier_name"] or "-",
                     width=170, anchor="w",
                     font=font(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=3)

        ctk.CTkLabel(row, text=f"₱{p['total_cost']:.2f}",
                     width=90, anchor="w",
                     font=font_bold(11),
                     text_color=FG_PRIMARY).pack(side="left", padx=3)

        # ---- Status color-coded ----
        status = p["status"]
        colors = {
            "Ordered":   BRAND_YELLOW,
            "Received":  BRAND_GREEN,
            "Cancelled": DANGER,
        }
        ctk.CTkLabel(row, text=status, width=100, anchor="w",
                     font=font_bold(11),
                     text_color=colors.get(status, FG_SECONDARY)
                     ).pack(side="left", padx=3)

        ctk.CTkLabel(row, text=p["full_name"] or p["username"] or "-",
                     width=120, anchor="w",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=3)

        ctk.CTkLabel(row, text=(p["created_at"] or "")[:10],
                     width=130, anchor="w",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=3)

        ctk.CTkLabel(row, text=(p["received_at"] or "-")[:10],
                     width=130, anchor="w",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(side="left", padx=3)

        # ---- Actions ----
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=4)

        ctk.CTkButton(actions, text="View", width=60, height=28,
                      corner_radius=6,
                      font=font_bold(11),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=lambda pur=p: self._view_dialog(pur)
                      ).pack(side="left", padx=2)

        if status == "Ordered":
            ctk.CTkButton(actions, text="Receive", width=70, height=28,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=BRAND_GREEN, hover_color="#1E9040",
                          command=lambda pur=p: self._receive(pur)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(actions, text="Cancel", width=70, height=28,
                          corner_radius=6,
                          font=font_bold(11),
                          fg_color=DANGER, hover_color=DANGER_HOVER,
                          command=lambda pur=p: self._cancel(pur)
                          ).pack(side="left", padx=2)

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def _receive(self, purchase):
        confirm = messagebox.askyesno(
            "Receive Purchase Order",
            f"Mark PO #{purchase['purchase_id']} as Received?\n\n"
            "The ordered quantities will be added to inventory."
        )
        if not confirm:
            return

        ok, msg = PurchaseController.receive(self.user, purchase["purchase_id"])
        if ok:
            messagebox.showinfo("Received", msg)
            self._load()
        else:
            messagebox.showerror("Error", msg)

    def _cancel(self, purchase):
        confirm = messagebox.askyesno(
            "Cancel Purchase Order",
            f"Cancel PO #{purchase['purchase_id']}?"
        )
        if not confirm:
            return

        ok, msg = PurchaseController.cancel(self.user, purchase["purchase_id"])
        if ok:
            self._load()
        else:
            messagebox.showerror("Error", msg)

    # ─────────────────────────────────────────────
    # DIALOGS
    # ─────────────────────────────────────────────

    def _new_po_dialog(self):
        PurchaseOrderDialog(self.winfo_toplevel(), self.user, on_save=self._load)

    def _view_dialog(self, purchase):
        PurchaseDetailDialog(self.winfo_toplevel(), purchase)


# ─────────────────────────────────────────────
# NEW PURCHASE ORDER DIALOG (styled)
# ─────────────────────────────────────────────

class PurchaseOrderDialog(ctk.CTkToplevel):

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, user, on_save):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.on_save = on_save
        self.title("New Purchase Order")
        self.geometry("820x580")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)

        self.suppliers = SupplierController.list_suppliers()
        self.cart = []

        self._build()
        prepare_dialog_screen(self, self.parent)

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        ctk.CTkLabel(self, text="New Purchase Order",
                     font=font_bold(18),
                     text_color=FG_PRIMARY).pack(pady=(18, 4))

        ctk.CTkLabel(self, text="Select a supplier, then add products to order",
                     font=font(11),
                     text_color=FG_SECONDARY).pack(pady=(0, 12))

        # ---- Supplier picker card ----
        sup_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                corner_radius=10,
                                border_width=1,
                                border_color=BORDER)
        sup_card.pack(fill="x", padx=20, pady=(0, 10))

        sup_row = ctk.CTkFrame(sup_card, fg_color="transparent")
        sup_row.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(sup_row, text="SUPPLIER",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(side="left", padx=(0, 10))

        self.supplier_names = [s["name"] for s in self.suppliers] or ["(No suppliers)"]
        self.supplier_var = ctk.StringVar(value=self.supplier_names[0])
        self.supplier_menu = ctk.CTkOptionMenu(
            sup_row, values=self.supplier_names,
            variable=self.supplier_var,
            width=280, height=36,
            corner_radius=8,
            font=font(12),
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=NEUTRAL,
            text_color=FG_PRIMARY,
            command=self._on_supplier_change,
        )
        self.supplier_menu.pack(side="left", padx=(0, 10))

        ctk.CTkButton(sup_row, text="Refresh", width=100, height=36,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._load_products_for_supplier
                      ).pack(side="left")

        # ---- Two-column body ----
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        # ---- Left card: products ----
        left = ctk.CTkFrame(body, fg_color=BG_CARD,
                            corner_radius=10,
                            border_width=1,
                            border_color=BORDER)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        ctk.CTkLabel(left, text="Products of Supplier",
                     font=font_bold(12),
                     text_color=FG_PRIMARY).pack(pady=(12, 4))

        self.products_frame = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.products_frame.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        # ---- Right card: order lines ----
        right = ctk.CTkFrame(body, fg_color=BG_CARD,
                             corner_radius=10,
                             border_width=1,
                             border_color=BORDER)
        right.pack(side="right", fill="both", expand=True, padx=(6, 0))

        ctk.CTkLabel(right, text="Order Lines",
                     font=font_bold(12),
                     text_color=FG_PRIMARY).pack(pady=(12, 4))

        self.lines_frame = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.lines_frame.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        # ---- Total ----
        total_row = ctk.CTkFrame(self, fg_color="transparent")
        total_row.pack(fill="x", padx=20, pady=(0, 4))

        ctk.CTkLabel(total_row, text="TOTAL",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(side="left")

        self.total_label = ctk.CTkLabel(total_row, text="₱0.00",
                                        font=font_bold(18),
                                        text_color=ACCENT)
        self.total_label.pack(side="right")

        # ---- Notes ----
        notes_row = ctk.CTkFrame(self, fg_color="transparent")
        notes_row.pack(fill="x", padx=20, pady=(4, 8))

        ctk.CTkLabel(notes_row, text="NOTES",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(anchor="w", pady=(0, 4))

        self.notes_e = ctk.CTkEntry(notes_row, height=36,
                                    corner_radius=8,
                                    font=font(12),
                                    fg_color=BG_INPUT,
                                    border_color=BORDER,
                                    border_width=1,
                                    placeholder_text="Optional notes for this order")
        self.notes_e.pack(fill="x")

        # ---- Buttons ----
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(6, 18))

        ctk.CTkButton(btn_row, text="Create Order",
                      width=160, height=40,
                      corner_radius=8,
                      font=font_bold(13),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._save).pack(side="left", padx=6)

        ctk.CTkButton(btn_row, text="Clear",
                      width=100, height=40,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self._clear).pack(side="left", padx=6)

        # ---- Auto-load ----
        self._load_products_for_supplier()

    # ─────────────────────────────────────────────
    # SUPPLIER CHANGE
    # ─────────────────────────────────────────────

    def _on_supplier_change(self, choice):
        self._load_products_for_supplier()

    # ─────────────────────────────────────────────
    # RESOLVE SELECTED SUPPLIER ID
    # ─────────────────────────────────────────────

    def _get_selected_supplier_id(self):
        supplier_name = self.supplier_var.get()
        for s in self.suppliers:
            if s["name"] == supplier_name:
                return s["supplier_id"]
        return None

    # ─────────────────────────────────────────────
    # LOAD PRODUCTS FOR SELECTED SUPPLIER
    # ─────────────────────────────────────────────

    def _load_products_for_supplier(self):
        for w in self.products_frame.winfo_children():
            w.destroy()

        supplier_id = self._get_selected_supplier_id()
        if supplier_id is None:
            ctk.CTkLabel(self.products_frame,
                         text="(no supplier selected)",
                         font=font(11),
                         text_color=FG_MUTED).pack(pady=10)
            return

        products = InventoryController.list_by_supplier(supplier_id)

        if not products:
            ctk.CTkLabel(self.products_frame,
                         text="No products for this supplier.",
                         font=font(11),
                         text_color=FG_MUTED).pack(pady=10)
            return

        for p in products:
            ctk.CTkButton(
                self.products_frame,
                text=f"  {p['name']}  ({p['product_code']})",
                anchor="w",
                height=38,
                corner_radius=8,
                font=font(12),
                fg_color=BG_INPUT,
                hover_color="#EAF0FF",
                text_color=FG_PRIMARY,
                border_width=1,
                border_color=BORDER,
                command=lambda prod=p: self._add_line(prod)
            ).pack(fill="x", pady=3)

    # ─────────────────────────────────────────────
    # ADD A LINE
    # ─────────────────────────────────────────────

    def _add_line(self, product):
        for line in self.cart:
            if line["product_id"] == product["product_id"]:
                messagebox.showinfo("Already added",
                                    f"{product['name']} is already in the order.")
                return

        # ---- Quantity / cost prompt ----
        prompt = ctk.CTkToplevel(self)
        prompt.title(f"Add {product['name']}")
        prompt.geometry("360x320")
        prompt.resizable(False, False)
        prompt.configure(fg_color=BG_MAIN)

        ctk.CTkLabel(prompt, text=product["name"],
                     font=font_bold(14),
                     text_color=FG_PRIMARY).pack(pady=(20, 4))

        ctk.CTkLabel(prompt, text=product["product_code"],
                     font=font(11),
                     text_color=FG_SECONDARY).pack(pady=(0, 14))

        ctk.CTkLabel(prompt, text="QUANTITY",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(anchor="w", padx=30, pady=(0, 4))

        qty_e = ctk.CTkEntry(prompt, width=300, height=36,
                             corner_radius=8,
                             font=font(12),
                             fg_color=BG_INPUT,
                             border_color=BORDER,
                             border_width=1)
        qty_e.pack(padx=30)
        qty_e.insert(0, "1")

        ctk.CTkLabel(prompt, text="UNIT COST (₱)",
                     font=font_bold(10),
                     text_color=FG_SECONDARY).pack(anchor="w", padx=30, pady=(12, 4))

        cost_e = ctk.CTkEntry(prompt, width=300, height=36,
                              corner_radius=8,
                              font=font(12),
                              fg_color=BG_INPUT,
                              border_color=BORDER,
                              border_width=1)
        cost_e.pack(padx=30)
        cost_e.insert(0, f"{product['price']:.2f}")

        def save():
            try:
                qty = int(qty_e.get())
                cost = float(cost_e.get())
                if qty <= 0 or cost < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Enter valid quantity and cost.")
                return

            self.cart.append({
                "product_id": product["product_id"],
                "name":       product["name"],
                "code":       product["product_code"],
                "quantity":   qty,
                "cost":       cost,
            })
            prompt.destroy()
            self._render_lines()

        ctk.CTkButton(prompt, text="Add",
                      width=300, height=40,
                      corner_radius=8,
                      font=font_bold(13),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=save).pack(pady=(20, 20))
        prepare_dialog_screen(prompt, self)

    # ─────────────────────────────────────────────
    # RENDER LINES
    # ─────────────────────────────────────────────

    def _render_lines(self):
        for w in self.lines_frame.winfo_children():
            w.destroy()

        if not self.cart:
            ctk.CTkLabel(self.lines_frame,
                         text="No items yet",
                         font=font(11),
                         text_color=FG_MUTED).pack(pady=20)
            self.total_label.configure(text="₱0.00")
            return

        for i, line in enumerate(self.cart):
            bg = BG_ROW_ALT if i % 2 else BG_CARD

            row = ctk.CTkFrame(self.lines_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=line["name"], width=140,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=(8, 3), pady=6)

            ctk.CTkLabel(row, text=f"×{line['quantity']}",
                         width=40,
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=f"₱{line['cost']:.2f}",
                         width=70,
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

            subtotal = line["quantity"] * line["cost"]
            ctk.CTkLabel(row, text=f"₱{subtotal:.2f}",
                         width=80,
                         font=font_bold(11),
                         text_color=ACCENT).pack(side="left", padx=3)

            ctk.CTkButton(row, text="✕", width=28, height=28,
                          corner_radius=6,
                          font=font(11),
                          fg_color=DANGER, hover_color=DANGER_HOVER,
                          command=lambda pid=line["product_id"]:
                              self._remove_line(pid)
                          ).pack(side="right", padx=8, pady=4)

        total = sum(l["quantity"] * l["cost"] for l in self.cart)
        self.total_label.configure(text=f"₱{total:.2f}")

    def _remove_line(self, product_id):
        self.cart = [l for l in self.cart if l["product_id"] != product_id]
        self._render_lines()

    def _clear(self):
        self.cart.clear()
        self._render_lines()

    # ─────────────────────────────────────────────
    # SAVE
    # ─────────────────────────────────────────────

    def _save(self):
        if not self.cart:
            messagebox.showerror("Error", "Add at least one product to the order.")
            return

        supplier_id = self._get_selected_supplier_id()
        if supplier_id is None:
            messagebox.showerror("Error", "Please select a supplier.")
            return

        items = [{
            "product_id": l["product_id"],
            "quantity":   l["quantity"],
            "cost":       l["cost"],
        } for l in self.cart]

        ok, result = PurchaseController.create(
            self.user, supplier_id, items, self.notes_e.get().strip()
        )
        if ok:
            messagebox.showinfo("Purchase Order Created",
                                f"PO #{result} created with {len(items)} item(s).")
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", result)


# ─────────────────────────────────────────────
# PURCHASE DETAIL DIALOG (styled)
# ─────────────────────────────────────────────

class PurchaseDetailDialog(ctk.CTkToplevel):

    # ─────────────────────────────────────────────
    # SETUP
    # ─────────────────────────────────────────────

    def __init__(self, parent, purchase):
        super().__init__(parent)
        self.parent = parent
        self.purchase = purchase
        self.title(f"PO #{purchase['purchase_id']}")
        self.geometry("660x520")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self._build()
        prepare_dialog_screen(self, self.parent)

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        p = self.purchase

        ctk.CTkLabel(self, text=f"Purchase Order #{p['purchase_id']}",
                     font=font_bold(18),
                     text_color=FG_PRIMARY).pack(pady=(18, 4))

        ctk.CTkLabel(self,
                     text=p["supplier_name"] or "Unknown Supplier",
                     font=font(12),
                     text_color=FG_SECONDARY).pack(pady=(0, 14))

        # ---- Info card ----
        info = ctk.CTkFrame(self, fg_color=BG_CARD,
                            corner_radius=12,
                            border_width=1,
                            border_color=BORDER)
        info.pack(fill="x", padx=20, pady=(0, 10))

        rows = [
            ("Status",        p["status"]),
            ("Total",         f"₱{p['total_cost']:.2f}"),
            ("Ordered By",    p["full_name"] or p["username"]),
            ("Date Ordered",  p["created_at"]),
            ("Date Received", p["received_at"] or "-"),
            ("Notes",         p["notes"] or "-"),
        ]
        for i, (label, value) in enumerate(rows):
            if i > 0:
                ctk.CTkFrame(info, height=1, fg_color=BORDER).pack(
                    fill="x", padx=14)

            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=8)

            ctk.CTkLabel(row, text=label,
                         width=120, anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left")

            ctk.CTkLabel(row, text=str(value), anchor="w",
                         font=font(12),
                         text_color=FG_PRIMARY).pack(side="left")

        # ---- Items card ----
        items_card = ctk.CTkFrame(self, fg_color=BG_CARD,
                                  corner_radius=12,
                                  border_width=1,
                                  border_color=BORDER)
        items_card.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        ctk.CTkLabel(items_card, text="Items",
                     font=font_bold(13),
                     text_color=FG_PRIMARY).pack(pady=(12, 4))

        lines = ctk.CTkScrollableFrame(items_card, fg_color="transparent")
        lines.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        # ---- Header ----
        header = ctk.CTkFrame(lines, fg_color="transparent")
        header.pack(fill="x", pady=(4, 8))
        for text, width in [("Code", 90), ("Name", 200),
                            ("Qty", 60), ("Cost", 90), ("Subtotal", 100)]:
            ctk.CTkLabel(header, text=text, width=width,
                         anchor="w",
                         font=font_bold(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

        # ---- Items ----
        items = PurchaseController.get_items(p["purchase_id"])
        for i, it in enumerate(items):
            bg = BG_ROW_ALT if i % 2 else BG_CARD

            row = ctk.CTkFrame(lines, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=it["product_code"] or "-",
                         width=90, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3, pady=6)

            ctk.CTkLabel(row, text=it["product_name"],
                         width=200, anchor="w",
                         font=font_bold(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=str(it["quantity"]),
                         width=60, anchor="w",
                         font=font(11),
                         text_color=FG_PRIMARY).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=f"₱{it['cost']:.2f}",
                         width=90, anchor="w",
                         font=font(11),
                         text_color=FG_SECONDARY).pack(side="left", padx=3)

            ctk.CTkLabel(row, text=f"₱{it['quantity'] * it['cost']:.2f}",
                         width=100, anchor="w",
                         font=font_bold(11),
                         text_color=ACCENT).pack(side="left", padx=3)

        # ---- Close ----
        ctk.CTkButton(self, text="Close",
                      width=120, height=38,
                      corner_radius=8,
                      font=font_bold(12),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self.destroy).pack(pady=(0, 16))