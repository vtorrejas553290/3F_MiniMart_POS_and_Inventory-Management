# ─────────────────────────────────────────────
# INVENTORY REPORT — preview dialog
# ─────────────────────────────────────────────

from tkinter import messagebox
import customtkinter as ctk

from utils import prepare_dialog_screen
from utils_pkg.inventory_report import (
    build_inventory_report_data, render_inventory_report_text,
    export_inventory_pdf,
)
from config import (
    font, font_bold,
    BG_MAIN, BG_CARD, BORDER,
    FG_PRIMARY, FG_SECONDARY,
    BRAND_GREEN,
    NEUTRAL, NEUTRAL_HOVER, NEUTRAL_TEXT,
)


class InventoryReportDialog(ctk.CTkToplevel):

    MONO_FONT = ("Consolas", 10)

    def __init__(self, parent, products, filters, exporter_name=""):
        super().__init__(parent)
        self.parent = parent
        self.products = products
        self.filters = filters
        self.exporter_name = exporter_name
        self.data = None

        self.title("Inventory Report Preview")
        self.geometry("900x700")
        self.resizable(True, True)
        self.minsize(700, 500)
        self.configure(fg_color=BG_MAIN)

        self._build()
        prepare_dialog_screen(self, self.parent)

        self.transient(parent)
        self.grab_set()
        self.focus_force()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(header, text="Inventory Report — Preview",
                     font=font_bold(15),
                     text_color=FG_PRIMARY,
                     anchor="w").pack(side="left")

        ctk.CTkButton(header, text="✕",
                      width=30, height=30,
                      corner_radius=6, font=font_bold(13),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self.destroy).pack(side="right")

        ctk.CTkLabel(self,
                     text="Review the report below, then click Save as PDF to export.",
                     font=font(11),
                     text_color=FG_SECONDARY,
                     anchor="w").pack(fill="x", padx=16, pady=(0, 8))

        # ---- Build data ----
        try:
            self.data = build_inventory_report_data(
                self.products, self.filters,
                exporter_name=self.exporter_name,
            )
        except Exception as e:
            ctk.CTkLabel(self,
                         text=f"Could not build report:\n{e}",
                         font=font(11),
                         text_color="#DC2626",
                         justify="left").pack(pady=20, padx=16)
            return

        # ---- Preview card ----
        card = ctk.CTkFrame(self, fg_color="#FFFFFF",
                            corner_radius=8, border_width=1,
                            border_color=BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        preview_frame = ctk.CTkScrollableFrame(
            card, fg_color="#FFFFFF", corner_radius=0,
        )
        preview_frame.pack(fill="both", expand=True, padx=6, pady=6)

        report_text = render_inventory_report_text(self.data)

        ctk.CTkLabel(
            preview_frame,
            text=report_text,
            font=self.MONO_FONT,
            text_color="#000000",
            justify="left",
            anchor="nw",
        ).pack(anchor="nw", padx=8, pady=8)

        # ---- Buttons ----
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(btn_row, text="Close",
                      width=120, height=40,
                      corner_radius=8, font=font_bold(12),
                      fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                      text_color=NEUTRAL_TEXT,
                      command=self.destroy).pack(side="left")

        ctk.CTkButton(btn_row, text="Save as PDF",
                      height=40, corner_radius=8, font=font_bold(12),
                      fg_color=BRAND_GREEN, hover_color="#1E9040",
                      command=self._save_pdf).pack(side="right", fill="x",
                                                   expand=True, padx=(8, 0))

    def _save_pdf(self):
        if self.data is None:
            messagebox.showerror("Error", "No report data to export.")
            return

        ok, result = export_inventory_pdf(self.data, parent_window=self.parent)
        if ok:
            messagebox.showinfo("Export Complete",
                                f"PDF saved to:\n{result}")
            self.destroy()
        elif result != "Cancelled.":
            messagebox.showerror("Export Failed", result)