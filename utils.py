# ─────────────────────────────────────────────
# UI UTILITIES (window centering, dialogs, maximize)
# ─────────────────────────────────────────────

import sys
import os
import shutil
import uuid
import customtkinter as ctk
from tkinter import filedialog


# ─────────────────────────────────────────────
# IMAGE UTILITIES (product picture handling)
# ─────────────────────────────────────────────

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "product_images")
os.makedirs(IMAGE_DIR, exist_ok=True)


def pick_image_file():
    """
    Open a file dialog for the user to choose an image.
    Returns the file path, or None if cancelled.
    """
    path = filedialog.askopenfilename(
        title="Select Product Image",
        filetypes=[
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("All files", "*.*"),
        ]
    )
    return path or None


def save_product_image(source_path):
    """
    Copy the selected image into the product_images folder
    with a unique filename. Returns the stored path.
    """
    if not source_path or not os.path.exists(source_path):
        return None

    ext = os.path.splitext(source_path)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(IMAGE_DIR, filename)

    shutil.copy2(source_path, dest)
    return dest


def delete_product_image(image_path):
    """Remove a product image file if it exists."""
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except OSError:
            pass


# ─────────────────────────────────────────────
# WINDOW SIZING
# ─────────────────────────────────────────────

def center_on_parent(window, parent):
    """
    Center a pop-up window on its parent window.
    Call AFTER widgets are built.
    """
    window.update_idletasks()

    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()

    win_w = window.winfo_width()
    win_h = window.winfo_height()

    x = parent_x + (parent_w - win_w) // 2
    y = parent_y + (parent_h - win_h) // 2

    window.geometry(f"{win_w}x{win_h}+{x}+{y}")


def center_on_screen(window):
    """
    Center a pop-up window on the screen.
    """
    window.update_idletasks()

    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()

    win_w = window.winfo_width()
    win_h = window.winfo_height()

    x = (screen_w - win_w) // 2
    y = (screen_h - win_h) // 2

    window.geometry(f"{win_w}x{win_h}+{x}+{y}")


# ─────────────────────────────────────────────
# MAXIMIZE (cross-platform)
# ─────────────────────────────────────────────

def maximize(window):
    if sys.platform.startswith("win"):
        window.state("zoomed")                  # ---- Windows ----
    elif sys.platform == "darwin":
        window.attributes("-zoomed", True)      # ---- macOS ----
    else:
        window.attributes("-zoomed", True)      # ---- Linux ----


# ─────────────────────────────────────────────
# DIALOG SETUP (fix z-order + centering)
# ─────────────────────────────────────────────

def prepare_dialog(dialog, parent):
    """
    Setup a CTkToplevel:
      - tied to the parent window (transient)
      - raised above the parent once
      - modal (grabs input)
      - centered on the PARENT window

    NOTE: We do NOT toggle -topmost here — that hides the X button on Windows.
    """
    dialog.transient(parent)                    # ---- tie to parent ----
    dialog.lift()                               # ---- raise above parent ----
    dialog.grab_set()                           # ---- capture all input ----
    dialog.focus_force()                        # ---- grab focus ----

    # ---- Center AFTER the window is fully built ----
    dialog.after(10, lambda: center_on_parent(dialog, parent))


def prepare_dialog_screen(dialog, parent):
    """
    Same as prepare_dialog(), but centers the dialog on the SCREEN
    instead of the parent window.
    """
    dialog.transient(parent)
    dialog.lift()
    dialog.grab_set()
    dialog.focus_force()

    # ---- Center on SCREEN after the window is fully built ----
    dialog.after(10, lambda: center_on_screen(dialog))


# ─────────────────────────────────────────────
# SAFE DIALOG BUILDER (optional convenience)
# ─────────────────────────────────────────────

def make_dialog(parent, title="Dialog", size="400x400", resizable=(False, False)):
    """
    Create a CTkToplevel ready for building:
      - sets title + geometry + resizable
      - returns the dialog (not yet centered)

    Usage:
        dlg = make_dialog(self, "My Dialog", "400x300")
        ... build widgets ...
        prepare_dialog_screen(dlg, self)
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry(size)
    dialog.resizable(*resizable)
    return dialog