# ─────────────────────────────────────────────
# USER MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local


# ─────────────────────────────────────────────
# HELPER — combine first / middle / last
# ─────────────────────────────────────────────

def _build_full_name(first, middle, last):
    """Join the name parts into a display name."""
    parts = [p for p in (first, middle, last) if p and p.strip()]
    return " ".join(parts)


def _row_with_full_name(row):
    """Return a dict with a computed `full_name` key."""
    if row is None:
        return None
    d = dict(row)
    d["full_name"] = _build_full_name(
        d.get("first_name"),
        d.get("middle_name"),
        d.get("last_name"),
    )
    return d


# ─────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────

def get_user_by_username(username):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1",
        (username,)
    ).fetchone()
    conn.close()
    return _row_with_full_name(row)


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return _row_with_full_name(row)


def get_all_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users ORDER BY role, username"
    ).fetchall()
    conn.close()
    return [_row_with_full_name(r) for r in rows]


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def username_exists(username):
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)",
        (username,)
    ).fetchone()
    conn.close()
    return row is not None


def create_user(username, password, first_name, middle_name, last_name, role):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO users
                (username, password, first_name, middle_name, last_name,
                 role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (username, password, first_name, middle_name, last_name,
              role, now_local()))
        conn.commit()
        return True, "User created."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_user(user_id, first_name, middle_name, last_name,
                role, is_active, password=None):
    conn = get_connection()
    try:
        if password:
            conn.execute("""
                UPDATE users
                SET first_name = ?, middle_name = ?, last_name = ?,
                    role = ?, is_active = ?, password = ?
                WHERE user_id = ?
            """, (first_name, middle_name, last_name,
                  role, is_active, password, user_id))
        else:
            conn.execute("""
                UPDATE users
                SET first_name = ?, middle_name = ?, last_name = ?,
                    role = ?, is_active = ?
                WHERE user_id = ?
            """, (first_name, middle_name, last_name,
                  role, is_active, user_id))
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