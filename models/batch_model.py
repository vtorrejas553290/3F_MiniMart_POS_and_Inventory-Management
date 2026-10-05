# ─────────────────────────────────────────────
# BATCH MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local


# ─────────────────────────────────────────────
# BATCH NUMBER GENERATOR
# ─────────────────────────────────────────────

def _next_batch_no(cur, product_id):
    row = cur.execute(
        "SELECT product_code FROM products WHERE product_id = ?",
        (product_id,)
    ).fetchone()
    product_code = row["product_code"] if row else f"PRD-{product_id:04d}"

    count = cur.execute(
        "SELECT COUNT(*) AS c FROM batches WHERE product_id = ?",
        (product_id,)
    ).fetchone()["c"]

    return f"{product_code}-B{count + 1:03d}"


# ─────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────

def create_batch(product_id, quantity, cost_price=0.0,
                 expiration_date=None, supplier_id=None,
                 purchase_id=None):
    if quantity <= 0:
        return False, "Quantity must be positive."

    conn = get_connection()
    try:
        cur = conn.cursor()
        batch_no = _next_batch_no(cur, product_id)
        now = now_local()

        cur.execute("""
            INSERT INTO batches
                (product_id, batch_no, quantity, cost_price,
                 expiration_date, supplier_id, purchase_id,
                 is_archived, received_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (product_id, batch_no, quantity, cost_price,
              expiration_date, supplier_id, purchase_id,
              now, now))

        batch_id = cur.lastrowid
        conn.commit()
        return True, batch_id
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def create_batch_cur(cur, product_id, quantity, cost_price=0.0,
                     expiration_date=None, supplier_id=None,
                     purchase_id=None):
    batch_no = _next_batch_no(cur, product_id)
    now = now_local()

    cur.execute("""
        INSERT INTO batches
            (product_id, batch_no, quantity, cost_price,
             expiration_date, supplier_id, purchase_id,
             is_archived, received_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (product_id, batch_no, quantity, cost_price,
          expiration_date, supplier_id, purchase_id,
          now, now))

    return cur.lastrowid


# ─────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────

def get_batches(product_id, include_archived=False):
    conn = get_connection()
    sql = "SELECT * FROM batches WHERE product_id = ?"
    if not include_archived:
        sql += " AND is_archived = 0"
    sql += """
        ORDER BY
            CASE WHEN expiration_date IS NULL THEN 1 ELSE 0 END,
            expiration_date ASC,
            received_at ASC
    """
    rows = conn.execute(sql, (product_id,)).fetchall()
    conn.close()
    return rows


def get_batch(batch_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM batches WHERE batch_id = ?",
        (batch_id,)
    ).fetchone()
    conn.close()
    return row


def get_available_batches_cur(cur, product_id):
    today = now_local()[:10]

    rows = cur.execute("""
        SELECT * FROM batches
        WHERE product_id = ?
          AND is_archived = 0
          AND quantity > 0
          AND (expiration_date IS NULL OR expiration_date >= ?)
        ORDER BY
            CASE WHEN expiration_date IS NULL THEN 1 ELSE 0 END,
            expiration_date ASC,
            received_at ASC
    """, (product_id, today)).fetchall()

    return rows


def get_expired_batches(product_id=None):
    conn = get_connection()
    today = now_local()[:10]

    sql = """
        SELECT b.*, p.name AS product_name, p.product_code
        FROM batches b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.is_archived = 0
          AND b.quantity > 0
          AND b.expiration_date IS NOT NULL
          AND b.expiration_date < ?
    """
    params = [today]
    if product_id is not None:
        sql += " AND b.product_id = ?"
        params.append(product_id)
    sql += " ORDER BY b.expiration_date ASC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def get_expiring_soon_batches(days=30, product_id=None):
    conn = get_connection()
    today = now_local()[:10]

    sql = """
        SELECT b.*, p.name AS product_name, p.product_code
        FROM batches b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.is_archived = 0
          AND b.quantity > 0
          AND b.expiration_date IS NOT NULL
          AND b.expiration_date >= ?
          AND b.expiration_date <= DATE(?, '+' || ? || ' days')
    """
    params = [today, today, days]
    if product_id is not None:
        sql += " AND b.product_id = ?"
        params.append(product_id)
    sql += " ORDER BY b.expiration_date ASC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def get_total_stock(product_id, include_expired=False):
    conn = get_connection()
    today = now_local()[:10]

    if include_expired:
        sql = """
            SELECT COALESCE(SUM(quantity), 0) AS total
            FROM batches
            WHERE product_id = ? AND is_archived = 0
        """
        params = (product_id,)
    else:
        sql = """
            SELECT COALESCE(SUM(quantity), 0) AS total
            FROM batches
            WHERE product_id = ?
              AND is_archived = 0
              AND (expiration_date IS NULL OR expiration_date >= ?)
        """
        params = (product_id, today)

    row = conn.execute(sql, params).fetchone()
    conn.close()
    return row["total"]


def get_total_stock_cur(cur, product_id, include_expired=False):
    today = now_local()[:10]

    if include_expired:
        row = cur.execute("""
            SELECT COALESCE(SUM(quantity), 0) AS total
            FROM batches
            WHERE product_id = ? AND is_archived = 0
        """, (product_id,)).fetchone()
    else:
        row = cur.execute("""
            SELECT COALESCE(SUM(quantity), 0) AS total
            FROM batches
            WHERE product_id = ?
              AND is_archived = 0
              AND (expiration_date IS NULL OR expiration_date >= ?)
        """, (product_id, today)).fetchone()

    return row["total"]


def get_earliest_expiration(product_id):
    conn = get_connection()
    today = now_local()[:10]

    row = conn.execute("""
        SELECT MIN(expiration_date) AS earliest
        FROM batches
        WHERE product_id = ?
          AND is_archived = 0
          AND quantity > 0
          AND expiration_date IS NOT NULL
          AND expiration_date >= ?
    """, (product_id, today)).fetchone()

    conn.close()
    return row["earliest"] if row else None


# ─────────────────────────────────────────────
# FEFO DEDUCTION
# ─────────────────────────────────────────────

def deduct_fefo_cur(cur, product_id, quantity, transaction_id):
    if quantity <= 0:
        return False, "Quantity must be positive.", 0

    product = cur.execute("""
        SELECT price FROM products WHERE product_id = ?
    """, (product_id,)).fetchone()

    if product is None:
        return False, "Product not found.", 0

    unit_price = product["price"]

    batches = get_available_batches_cur(cur, product_id)

    total_available = sum(b["quantity"] for b in batches)
    if total_available < quantity:
        return False, (
            f"Not enough sellable stock. "
            f"Requested: {quantity}, Available: {total_available}."
        ), 0

    remaining = quantity
    total_cost = 0.0

    for batch in batches:
        if remaining == 0:
            break

        take = min(batch["quantity"], remaining)
        if take <= 0:
            continue

        cur.execute("""
            UPDATE batches
            SET quantity = quantity - ?
            WHERE batch_id = ?
        """, (take, batch["batch_id"]))

        cost = batch["cost_price"] or 0
        subtotal = unit_price * take

        cur.execute("""
            INSERT INTO transaction_items
                (transaction_id, product_id, batch_id, quantity,
                 price, cost_price, subtotal)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (transaction_id, product_id, batch["batch_id"], take,
              unit_price, cost, subtotal))

        total_cost += cost * take
        remaining -= take

    if remaining > 0:
        return False, "Insufficient stock (race condition).", 0

    return True, "Stock deducted.", total_cost


# ─────────────────────────────────────────────
# ADJUSTMENTS
# ─────────────────────────────────────────────

def discard_batch(batch_id, quantity=None):
    conn = get_connection()
    try:
        cur = conn.cursor()

        if quantity is None:
            cur.execute("""
                UPDATE batches SET quantity = 0 WHERE batch_id = ?
            """, (batch_id,))
        else:
            cur.execute("""
                UPDATE batches
                SET quantity = MAX(0, quantity - ?)
                WHERE batch_id = ?
            """, (quantity, batch_id))

        conn.commit()
        return True, "Batch discarded."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def archive_batch(batch_id):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE batches SET is_archived = 1 WHERE batch_id = ?",
            (batch_id,)
        )
        conn.commit()
        return True, "Batch archived."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_batch(batch_id, quantity=None, cost_price=None,
                 expiration_date="__KEEP__"):
    """
    Update a batch's quantity, cost, and/or expiration date.

    Pass `expiration_date="__KEEP__"` (default) to leave it unchanged.
    Pass `expiration_date=None` to clear it.
    Pass a string like "2026-12-31" to set it.

    Returns (success, message).
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # ---- Verify batch exists ----
        row = cur.execute(
            "SELECT quantity, cost_price, expiration_date "
            "FROM batches WHERE batch_id = ?",
            (batch_id,)
        ).fetchone()
        if row is None:
            return False, "Batch not found."

        # ---- Build the update dynamically ----
        sets = []
        params = []

        if quantity is not None:
            if quantity < 0:
                return False, "Quantity cannot be negative."
            sets.append("quantity = ?")
            params.append(quantity)

        if cost_price is not None:
            if cost_price < 0:
                return False, "Cost cannot be negative."
            sets.append("cost_price = ?")
            params.append(cost_price)

        if expiration_date != "__KEEP__":
            sets.append("expiration_date = ?")
            params.append(expiration_date)

        if not sets:
            return True, "Nothing to update."

        params.append(batch_id)
        cur.execute(
            f"UPDATE batches SET {', '.join(sets)} WHERE batch_id = ?",
            params
        )
        conn.commit()
        return True, "Batch updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def count_expiring_soon(days=30):
    """Count non-expired batches expiring within `days` days, quantity > 0."""
    conn = get_connection()
    today = now_local()[:10]
    row = conn.execute("""
        SELECT COUNT(*) AS c
        FROM batches
        WHERE is_archived = 0
          AND quantity > 0
          AND expiration_date IS NOT NULL
          AND expiration_date >= ?
          AND expiration_date <= DATE(?, '+' || ? || ' days')
    """, (today, today, days)).fetchone()
    conn.close()
    return row["c"]


def count_expired():
    """Count batches already expired with quantity > 0."""
    conn = get_connection()
    today = now_local()[:10]
    row = conn.execute("""
        SELECT COUNT(*) AS c
        FROM batches
        WHERE is_archived = 0
          AND quantity > 0
          AND expiration_date IS NOT NULL
          AND expiration_date < ?
    """, (today,)).fetchone()
    conn.close()
    return row["c"]