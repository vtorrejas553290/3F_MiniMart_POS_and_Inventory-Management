# ─────────────────────────────────────────────
# USER MODEL
# ─────────────────────────────────────────────

from database import get_connection


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