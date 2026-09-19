# ─────────────────────────────────────────────
# SUPPLIER MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local


# ─────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────

def get_all_suppliers(include_archived=False):
    conn = get_connection()
    sql = """
        SELECT s.*, sc.name AS supplier_category_name
        FROM suppliers s
        JOIN supplier_categories sc
             ON s.supplier_category_id = sc.scat_id
    """
    if not include_archived:
        sql += " WHERE s.is_archived = 0"
    sql += " ORDER BY s.name"

    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows


def get_supplier(supplier_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM suppliers WHERE supplier_id = ?",
        (supplier_id,)
    ).fetchone()
    conn.close()
    return row


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def add_supplier(name, contact, address, supplier_category_id):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO suppliers
                (name, contact, address, supplier_category_id, is_archived, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (name, contact, address, supplier_category_id, now_local()))
        conn.commit()
        return True, "Supplier added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_supplier(supplier_id, name, contact, address, supplier_category_id):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE suppliers
            SET name = ?, contact = ?, address = ?, supplier_category_id = ?
            WHERE supplier_id = ?
        """, (name, contact, address, supplier_category_id, supplier_id))
        conn.commit()
        return True, "Supplier updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def archive_supplier(supplier_id):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE suppliers SET is_archived = 1 WHERE supplier_id = ?",
            (supplier_id,)
        )
        conn.commit()
        return True, "Supplier archived."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def unarchive_supplier(supplier_id):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE suppliers SET is_archived = 0 WHERE supplier_id = ?",
            (supplier_id,)
        )
        conn.commit()
        return True, "Supplier restored."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()