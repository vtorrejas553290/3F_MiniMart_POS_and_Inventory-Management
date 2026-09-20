# ─────────────────────────────────────────────
# USER MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local


# ---- Read ----

def get_user_by_username(username):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1",
        (username,)
    ).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return row


def get_all_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users ORDER BY role, username"
    ).fetchall()
    conn.close()
    return rows


# ---- Write ----

def create_user(username, password, full_name, role):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO users (username, password, full_name, role)
            VALUES (?, ?, ?, ?)
        """, (username, password, full_name, role))
        conn.commit()
        return True, "User created."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
# ─────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────

def get_all_users():
    """Return every user (sorted by role then username)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM users
        ORDER BY role, username
    """).fetchall()
    conn.close()
    return rows


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return row


def username_exists(username):
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)",
        (username,)
    ).fetchone()
    conn.close()
    return row is not None


def create_user(username, password, full_name, role):
    """Create a new user. Returns (success, message)."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO users (username, password, full_name, role,
                               is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (username, password, full_name, role, now_local()))
        conn.commit()
        return True, "User created."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_user(user_id, full_name, role, is_active, password=None):
    """Update a user. If password is None, keep the existing password."""
    conn = get_connection()
    try:
        if password:
            conn.execute("""
                UPDATE users
                SET full_name = ?, role = ?, is_active = ?, password = ?
                WHERE user_id = ?
            """, (full_name, role, is_active, password, user_id))
        else:
            conn.execute("""
                UPDATE users
                SET full_name = ?, role = ?, is_active = ?
                WHERE user_id = ?
            """, (full_name, role, is_active, user_id))
        conn.commit()
        return True, "User updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def set_user_active(user_id, is_active):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET is_active = ? WHERE user_id = ?",
            (is_active, user_id)
        )
        conn.commit()
        return True, "Status updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()