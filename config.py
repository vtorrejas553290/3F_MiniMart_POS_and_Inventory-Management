# ─────────────────────────────────────────────
# APPLICATION CONFIGURATION
# ─────────────────────────────────────────────

import os

# ---- App identity ----
APP_NAME = "3F MiniMart"
DB_PATH = os.path.join(os.path.dirname(__file__), "store_data.db")

# ---- User roles ----
ROLE_ADMIN = "admin"
ROLE_STAFF = "staff"

# ---- UI theme ----
APPEARANCE_MODE = "light"
COLOR_THEME = "blue"
WINDOW_SIZE = "1200x700"

# ---- Business defaults ----
DEFAULT_LOW_STOCK = 10

# ---- Payment methods ----
PAYMENT_CASH = "Cash"
PAYMENT_GCASH = "GCash"


# ─────────────────────────────────────────────
# UI DESIGN TOKENS — 3F MiniMart (SOFTENED)
# ─────────────────────────────────────────────
#
# Same brand hues as the store sign (green, blue, yellow),
# but desaturated for long-term desktop use.
#
# Signboard:     100% saturation  →  seen from far away
# Desktop app:   40-60% saturation  →  seen 8 hours a day
#
# Rule: use brand colors as ACCENTS, not as large surface fills.

# ---- Font family ----
FONT_FAMILY = "Segoe UI"

# ---- Font sizes ----
FONT_BRAND    = 26
FONT_H1       = 20
FONT_H2       = 15
FONT_BODY     = 13
FONT_SMALL    = 11
FONT_BUTTON   = 13


def font(size=FONT_BODY, weight="normal"):
    """Return a font tuple for CustomTkinter."""
    return (FONT_FAMILY, size, weight)


def font_bold(size=FONT_BODY):
    return (FONT_FAMILY, size, "bold")


# ─────────────────────────────────────────────
# BRAND HUES (softened for UI)
# ─────────────────────────────────────────────

BRAND_GREEN      = "#22A647"    # ---- calm brand green (was #3EE742) ----
BRAND_GREEN_DARK = "#166534"    # ---- deep green for contrast text ----
BRAND_BLUE       = "#3B6FD4"    # ---- softened brand blue (was #2755DD) ----
BRAND_YELLOW     = "#F5C842"    # ---- warm amber (was #F9F35A) ----

# ---- Raw brand colors (kept for reference/logo use only) ----
BRAND_GREEN_RAW  = "#3EE742"
BRAND_BLUE_RAW   = "#2755DD"
BRAND_YELLOW_RAW = "#F9F35A"


# ─────────────────────────────────────────────
# BACKGROUNDS
# ─────────────────────────────────────────────

BG_MAIN          = "#F5F7FA"    # ---- soft neutral ----
BG_CARD          = "#FFFFFF"    # ---- clean white cards ----
BG_SIDEBAR       = "#1E3A8A"    # ---- deep navy (was bright blue) ----
BG_SIDEBAR_ITEM  = "#2E4FAF"    # ---- active nav bg ----
BG_SIDEBAR_HOVER = "#3355B5"    # ---- hover ----
BG_INPUT         = "#F8FAFC"
BG_ROW_ALT       = "#F8FAFC"


# ─────────────────────────────────────────────
# TEXT
# ─────────────────────────────────────────────

FG_PRIMARY       = "#0F172A"    # ---- dark slate ----
FG_SECONDARY     = "#64748B"
FG_MUTED         = "#94A3B8"
FG_ON_BRAND      = "#FFFFFF"    # ---- text on green/blue ----


# ─────────────────────────────────────────────
# BUTTONS & ACCENTS
# ─────────────────────────────────────────────

ACCENT           = "#3B6FD4"    # ---- primary button (soft blue) ----
ACCENT_HOVER     = "#2E5BC0"
SUCCESS          = "#16A34A"    # ---- standard success green ----
SUCCESS_HOVER    = "#15803D"
WARNING          = "#F59E0B"    # ---- amber (was neon yellow) ----
DANGER           = "#DC2626"
DANGER_HOVER     = "#B91C1C"
NEUTRAL          = "#E2E8F0"
NEUTRAL_HOVER    = "#CBD5E1"
NEUTRAL_TEXT     = "#0F172A"


# ─────────────────────────────────────────────
# BORDERS & TINTS
# ─────────────────────────────────────────────

BORDER           = "#E2E8F0"
BG_BLUE_TINT     = "#EAF0FF"    # ---- subtle hover tint ----
BG_GREEN_TINT    = "#E9FBEA"    # ---- success tint ----
BG_YELLOW_TINT   = "#FEF3C7"    # ---- warning tint ----