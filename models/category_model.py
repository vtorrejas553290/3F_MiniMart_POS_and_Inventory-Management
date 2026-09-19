# ─────────────────────────────────────────────
# CATEGORY MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local


# ─────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────

def get_all_categories():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM categories ORDER BY name"
    ).fetchall()
    conn.close()
    return rows


def get_category(category_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM categories WHERE category_id = ?",
        (category_id,)
    ).fetchone()
    conn.close()
    return row


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def add_category(name, description=""):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO categories (name, description, created_at)
            VALUES (?, ?, ?)
        """, (name, description, now_local()))
        conn.commit()
        return True, "Category added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_category(category_id, name, description=""):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE categories SET name = ?, description = ?
            WHERE category_id = ?
        """, (name, description, category_id))
        conn.commit()
        return True, "Category updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()