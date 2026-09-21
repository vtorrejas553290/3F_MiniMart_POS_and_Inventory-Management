# ─────────────────────────────────────────────
# USER CONTROLLER (admin only)
# ─────────────────────────────────────────────

from models.user_model import (
    get_all_users, get_user_by_id,
    username_exists, create_user, update_user, set_user_active,
)
from models.activity_log_model import log_action


# ---- Minimum password length ----
MIN_PASSWORD_LENGTH = 6


class UserController:

    # ─────────────────────────────────────────────
    # READS
    # ─────────────────────────────────────────────

    @staticmethod
    def list_users():
        return get_all_users()

    @staticmethod
    def get_user(user_id):
        return get_user_by_id(user_id)

    # ─────────────────────────────────────────────
    # WRITES
    # ─────────────────────────────────────────────

    @staticmethod
    def add_user(admin_user, username, password,
                 first_name, middle_name, last_name):
        """
        Create a new STAFF user.
        Role is always 'staff' — admin accounts can only be added in the DB.
        """
        username = username.strip().lower()
        first_name = first_name.strip()
        middle_name = (middle_name or "").strip() or None
        last_name = last_name.strip()

        # ---- Validation ----
        if not username:
            return False, "Username is required."
        if not first_name:
            return False, "First name is required."
        if not last_name:
            return False, "Last name is required."
        if not password:
            return False, "Password is required."
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        if username_exists(username):
            return False, f"Username '{username}' is already taken."

        ok, msg = create_user(username, password,
                              first_name, middle_name, last_name,
                              "staff")
        if ok:
            log_action(admin_user["user_id"], "ADD_USER", f"{username} (staff)")
        return ok, msg

    @staticmethod
    def edit_user(admin_user, user_id,
                  first_name, middle_name, last_name,
                  new_password=None):
        """
        Update a user's name and optionally their password.
        Role is intentionally NOT editable — staff stay staff.
        """
        first_name = first_name.strip()
        middle_name = (middle_name or "").strip() or None
        last_name = last_name.strip()

        if not first_name:
            return False, "First name is required."
        if not last_name:
            return False, "Last name is required."
        if new_password is not None and len(new_password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."

        user = get_user_by_id(user_id)
        if not user:
            return False, "User not found."

        # ---- Protect admin accounts ----
        if user["role"] == "admin":
            return False, "Admin accounts cannot be edited from this screen."

        ok, msg = update_user(
            user_id,
            first_name, middle_name, last_name,
            user["role"],
            user["is_active"],
            new_password,
        )
        if ok:
            full = " ".join(p for p in (first_name, middle_name, last_name) if p)
            log_action(admin_user["user_id"], "UPDATE_USER",
                       f"ID {user_id} - {full}")
        return ok, msg

    @staticmethod
    def toggle_active(admin_user, user_id):
        """Enable or disable a staff account."""
        if user_id == admin_user["user_id"]:
            return False, "You cannot deactivate your own account."

        user = get_user_by_id(user_id)
        if not user:
            return False, "User not found."
        if user["role"] == "admin":
            return False, "Admin accounts cannot be deactivated."

        new_state = 0 if user["is_active"] else 1
        ok, msg = set_user_active(user_id, new_state)
        if ok:
            action = "ACTIVATE_USER" if new_state else "DEACTIVATE_USER"
            log_action(admin_user["user_id"], action,
                       f"ID {user_id} - {user['username']}")
        return ok, msg