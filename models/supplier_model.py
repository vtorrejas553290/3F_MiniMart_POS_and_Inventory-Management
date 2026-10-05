# ─────────────────────────────────────────────
# SUPPLIER MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _build_contact_person(first, middle, last):
    parts = [p for p in (first, middle, last) if p and p.strip()]
    return " ".join(parts)


def _row_with_contact_person(row):
    if row is None:
        return None
    d = dict(row)
    d["contact_person"] = _build_contact_person(
        d.get("contact_person_first"),
        d.get("contact_person_middle"),
        d.get("contact_person_last"),
    )
    return d


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
    return [_row_with_contact_person(r) for r in rows]


def get_supplier(supplier_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT s.*, sc.name AS supplier_category_name
        FROM suppliers s
        JOIN supplier_categories sc
             ON s.supplier_category_id = sc.scat_id
        WHERE s.supplier_id = ?
    """, (supplier_id,)).fetchone()
    conn.close()
    return _row_with_contact_person(row)


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def add_supplier(name, contact_number, supplier_category_id,
                 contact_person_first=None,
                 contact_person_middle=None,
                 contact_person_last=None,
                 address=None):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO suppliers
                (name, contact_number, supplier_category_id,
                 contact_person_first, contact_person_middle,
                 contact_person_last, address,
                 is_archived, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
        """, (name, contact_number, supplier_category_id,
              contact_person_first, contact_person_middle,
              contact_person_last, address, now_local()))
        conn.commit()
        return True, "Supplier added."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_supplier(supplier_id, name, contact_number, supplier_category_id,
                    contact_person_first=None,
                    contact_person_middle=None,
                    contact_person_last=None,
                    address=None):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE suppliers
            SET name = ?, contact_number = ?, supplier_category_id = ?,
                contact_person_first = ?, contact_person_middle = ?,
                contact_person_last = ?, address = ?
            WHERE supplier_id = ?
        """, (name, contact_number, supplier_category_id,
              contact_person_first, contact_person_middle,
              contact_person_last, address, supplier_id))
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