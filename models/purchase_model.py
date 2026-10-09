# ─────────────────────────────────────────────
# PURCHASE MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local
from models.batch_model import create_batch_cur


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _full_name_sql(alias="u"):
    return (
        f"TRIM("
        f"COALESCE({alias}.first_name, '') || ' ' || "
        f"COALESCE({alias}.middle_name || ' ', '') || "
        f"COALESCE({alias}.last_name, '')"
        f") AS full_name"
    )


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def create_purchase(supplier_id, user_id, items, notes=""):
    """
    Create a Purchase Order (status = 'Ordered').
    items = list of dicts: {product_id, quantity, cost, expiration_date}
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
                INSERT INTO purchase_items
                    (purchase_id, product_id, quantity, cost, expiration_date)
                VALUES (?, ?, ?, ?, ?)
            """, (pid, i["product_id"], i["quantity"], i["cost"],
                  i.get("expiration_date")))

        conn.commit()
        return True, pid

    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def receive_purchase(purchase_id, user_id, product_ids=None):
    """
    Mark a purchase order as Received and add its items to inventory.

    Parameters
    ----------
    purchase_id : int
        The purchase order ID.
    user_id : int
        The user performing the action.
    product_ids : list[int] | None
        If provided, only items whose product_id is in this list will be
        received (batches created, stock updated).
        If None, all items are received (original behavior).

    Returns
    -------
    (ok, message) : tuple[bool, str]
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # ---- 1. Load the PO ----
        row = cur.execute(
            "SELECT status, supplier_id FROM purchases WHERE purchase_id = ?",
            (purchase_id,)
        ).fetchone()

        if not row:
            return False, "Purchase not found."
        if row["status"] != "Ordered":
            return False, f"Purchase is already '{row['status']}'."

        supplier_id = row["supplier_id"]

        # ---- 2. Load all items on the PO ----
        all_items = cur.execute("""
            SELECT product_id, quantity, cost, expiration_date
            FROM purchase_items
            WHERE purchase_id = ?
        """, (purchase_id,)).fetchall()

        if not all_items:
            return False, "Purchase has no items."

        # ---- 3. Filter items by product_ids (if provided) ----
        if product_ids is None:
            items_to_receive = list(all_items)
        else:
            wanted = set(product_ids)
            items_to_receive = [
                it for it in all_items if it["product_id"] in wanted
            ]

        if not items_to_receive:
            return False, "No items selected to receive."

        # ---- 4. Create batches + update cost for each selected item ----
        for item in items_to_receive:
            create_batch_cur(
                cur,
                product_id=item["product_id"],
                quantity=item["quantity"],
                cost_price=item["cost"],
                expiration_date=item["expiration_date"],
                supplier_id=supplier_id,
                purchase_id=purchase_id,
            )
            cur.execute("""
                UPDATE products
                SET cost_price = ?, updated_at = ?
                WHERE product_id = ?
            """, (item["cost"], now_local(), item["product_id"]))

        # ---- 5. Decide whether to mark the whole PO as Received ----
        #
        # If EVERY item on the PO is in the received set, mark it Received.
        # Otherwise, leave it as Ordered so remaining items can be received
        # in a later partial receipt.
        #
        all_ids       = {it["product_id"] for it in all_items}
        received_ids  = {it["product_id"] for it in items_to_receive}

        if all_ids.issubset(received_ids):
            cur.execute("""
                UPDATE purchases
                SET status = 'Received', received_at = ?
                WHERE purchase_id = ?
            """, (now_local(), purchase_id))
            msg = "Purchase fully received. Batches created."
        else:
            msg = (
                f"Partially received {len(items_to_receive)} of "
                f"{len(all_items)} item(s). Remaining items can still "
                f"be received later."
            )

        conn.commit()
        return True, msg

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
    sql = f"""
        SELECT pu.*,
               s.name AS supplier_name,
               u.username, {_full_name_sql('u')}
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
    row = conn.execute(f"""
        SELECT pu.*,
               s.name AS supplier_name,
               u.username, {_full_name_sql('u')}
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