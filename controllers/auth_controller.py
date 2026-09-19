# ─────────────────────────────────────────────
# AUTH CONTROLLER (login / logout / role check)
# ─────────────────────────────────────────────

from models.user_model import get_user_by_username
from models.activity_log_model import log_action


class AuthController:

    # ---- Session state ----
    current_user = None

    # ---- Login ----

    @staticmethod
    def login(username, password):
        user = get_user_by_username(username)
        if not user:
            return False, "Username not found."

        if user["password"] != password:
            return False, "Incorrect password."

        AuthController.current_user = dict(user)
        log_action(user["user_id"], "LOGIN", f"Role: {user['role']}")
        return True, "Login successful."

    # ---- Logout ----

    @staticmethod
    def logout():
        if AuthController.current_user:
            u = AuthController.current_user
            log_action(u["user_id"], "LOGOUT", "")
        AuthController.current_user = None

    # ---- Accessors ----

    @staticmethod
    def get_current_user():
        return AuthController.current_user

    @staticmethod
    def is_admin():
        u = AuthController.current_user
        return u is not None and u["role"] == "admin"

    @staticmethod
    def is_staff():
        u = AuthController.current_user
        return u is not None and u["role"] == "staff"