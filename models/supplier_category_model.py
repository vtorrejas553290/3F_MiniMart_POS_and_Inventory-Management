# ─────────────────────────────────────────────
# SUPPLIER CATEGORY MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local


# ─────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────

def get_all_supplier_categories():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM supplier_categories ORDER BY name"
    ).fetchall()
    conn.close()
    return rows


def get_supplier_category(scat_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM supplier_categories WHERE scat_id = ?",
        (scat_id,)
    ).fetchone()
    conn.close()
    return row


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def add_supplier_category(name, description=""):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO supplier_categories (name, description, created_at)
            VALUES (?, ?, ?)
        """, (name, description, now_local()))
        conn.commit()
        return True, "Supplier category added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_supplier_category(scat_id, name, description=""):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE supplier_categories
            SET name = ?, description = ?
            WHERE scat_id = ?
        """, (name, description, scat_id))
        conn.commit()
        return True, "Supplier category updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()