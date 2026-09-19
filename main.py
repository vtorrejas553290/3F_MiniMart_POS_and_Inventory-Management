# ─────────────────────────────────────────────
# APPLICATION ENTRY POINT
# ─────────────────────────────────────────────

import customtkinter as ctk
from config import APPEARANCE_MODE, COLOR_THEME
from database import initialize_database


def main():
    ctk.set_appearance_mode(APPEARANCE_MODE)
    ctk.set_default_color_theme(COLOR_THEME)

    initialize_database()

    from views.login_view import LoginView
    LoginView().mainloop()


if __name__ == "__main__":
    main()