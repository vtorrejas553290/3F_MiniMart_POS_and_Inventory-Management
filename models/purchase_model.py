# ─────────────────────────────────────────────
# PURCHASE MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local
from models.product_model import add_stock_cur


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def create_purchase(supplier_id, user_id, items, notes=""):
    """
    Create a Purchase Order (status = 'Ordered').
    items = list of dicts: {product_id, quantity, cost}
    Returns (success, purchase_id_or_error)
    """
    total = sum(i["quantity"] * i["cost"] for i in items)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO purchases
                (supplier_id, user_id, total_cost, status, notes, created_at)
            VALUES (?, ?, ?, 'Ordered', ?, ?)
        """, (supplier_id, user_id, total, notes, now_local()))
        pid = cur.lastrowid

        for i in items:
            cur.execute("""
                INSERT INTO purchase_items (purchase_id, product_id, quantity, cost)
                VALUES (?, ?, ?, ?)
            """, (pid, i["product_id"], i["quantity"], i["cost"]))

        conn.commit()
        return True, pid

    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def receive_purchase(purchase_id, user_id):
    """
    Mark a PO as received and add the ordered quantities to stock.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # ---- Confirm PO exists and is still 'Ordered' ----
        row = cur.execute(
            "SELECT status FROM purchases WHERE purchase_id = ?",
            (purchase_id,)
        ).fetchone()

        if not row:
            return False, "Purchase not found."
        if row["status"] != "Ordered":
            return False, f"Purchase is already '{row['status']}'."

        # ---- Add stock for each line ----
        items = cur.execute(
            "SELECT product_id, quantity FROM purchase_items WHERE purchase_id = ?",
            (purchase_id,)
        ).fetchall()

        for item in items:
            add_stock_cur(cur, item["product_id"], item["quantity"])

        # ---- Mark as received ----
        cur.execute("""
            UPDATE purchases
            SET status = 'Received', received_at = ?
            WHERE purchase_id = ?
        """, (now_local(), purchase_id))

        conn.commit()
        return True, "Purchase received. Stock updated."

    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def cancel_purchase(purchase_id):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE purchases SET status = 'Cancelled'
            WHERE purchase_id = ? AND status = 'Ordered'
        """, (purchase_id,))
        conn.commit()
        return True, "Purchase cancelled."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────

def get_all_purchases(status=None, supplier_id=None):
    conn = get_connection()
    sql = """
        SELECT pu.*,
               s.name AS supplier_name,
               u.username, u.full_name
        FROM purchases pu
        JOIN suppliers s ON pu.supplier_id = s.supplier_id
        JOIN users u     ON pu.user_id     = u.user_id
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND pu.status = ?"
        params.append(status)
    if supplier_id:
        sql += " AND pu.supplier_id = ?"
        params.append(supplier_id)
    sql += " ORDER BY pu.created_at DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def get_purchase(purchase_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT pu.*,
               s.name AS supplier_name,
               u.username, u.full_name
        FROM purchases pu
        JOIN suppliers s ON pu.supplier_id = s.supplier_id
        JOIN users u     ON pu.user_id     = u.user_id
        WHERE pu.purchase_id = ?
    """, (purchase_id,)).fetchone()
    conn.close()
    return row


def get_purchase_items(purchase_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT pi.*, p.name AS product_name, p.product_code
        FROM purchase_items pi
        JOIN products p ON pi.product_id = p.product_id
        WHERE pi.purchase_id = ?
    """, (purchase_id,)).fetchall()
    conn.close()
    return rows


def get_purchases_by_supplier(supplier_id):
    return get_all_purchases(supplier_id=supplier_id)