# ─────────────────────────────────────────────
# TRANSACTION MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local
from models.product_model import deduct_stock_cur


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def create_transaction(user_id, cart, payment_method, amount_paid):
    """
    cart = list of dicts: {product_id, name, price, quantity}
    Returns (success, transaction_id_or_error, change)
    """
    total = sum(item["price"] * item["quantity"] for item in cart)

    if payment_method == "Cash" and amount_paid < total:
        return False, "Insufficient payment.", 0

    change = amount_paid - total if payment_method == "Cash" else 0

    conn = get_connection()
    try:
        cur = conn.cursor()

        # ---- Insert transaction header ----
        cur.execute("""
            INSERT INTO transactions
                (user_id, total, payment_method, amount_paid, change_due, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, total, payment_method, amount_paid, change, now_local()))
        txn_id = cur.lastrowid

        # ---- Insert each item + deduct stock (same connection) ----
        for item in cart:
            subtotal = item["price"] * item["quantity"]
            cur.execute("""
                INSERT INTO transaction_items
                    (transaction_id, product_id, quantity, price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (txn_id, item["product_id"], item["quantity"],
                  item["price"], subtotal))
            deduct_stock_cur(cur, item["product_id"], item["quantity"])

        conn.commit()
        return True, txn_id, change

    except Exception as e:
        conn.rollback()
        return False, str(e), 0
    finally:
        conn.close()


# ─────────────────────────────────────────────
# READ — BASIC
# ─────────────────────────────────────────────

def get_sales_today():
    conn = get_connection()
    today = now_local()[:10]
    row = conn.execute("""
        SELECT COALESCE(SUM(total), 0) AS total_sales, COUNT(*) AS count
        FROM transactions
        WHERE DATE(created_at) = ?
    """, (today,)).fetchone()
    conn.close()
    return row


def get_sales_between(start_date, end_date):
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.*, u.username, u.full_name
        FROM transactions t
        JOIN users u ON t.user_id = u.user_id
        WHERE DATE(t.created_at) BETWEEN ? AND ?
        ORDER BY t.created_at DESC
    """, (start_date, end_date)).fetchall()
    conn.close()
    return rows


def get_transaction_items(transaction_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT ti.*, p.name AS product_name
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.product_id
        WHERE ti.transaction_id = ?
        ORDER BY ti.item_id
    """, (transaction_id,)).fetchall()
    conn.close()
    return rows


# ─────────────────────────────────────────────
# READ — FILTERED (for reports)
# ─────────────────────────────────────────────

def get_transactions_filtered(date_from=None, date_to=None,
                              search=None, payment_method=None):
    """
    Return transactions filtered by:
      - date range (YYYY-MM-DD)
      - search term (txn#, cashier, payment method, product name)
      - payment method ('Cash' or 'GCash')
    Each row includes cashier name and item count.
    """
    conn = get_connection()
    sql = """
        SELECT t.*,
               u.username, u.full_name,
               (SELECT COUNT(*) FROM transaction_items ti
                WHERE ti.transaction_id = t.transaction_id) AS item_count
        FROM transactions t
        JOIN users u ON t.user_id = u.user_id
        WHERE 1=1
    """
    params = []

    if date_from:
        sql += " AND DATE(t.created_at) >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND DATE(t.created_at) <= ?"
        params.append(date_to)
    if payment_method and payment_method != "All":
        sql += " AND t.payment_method = ?"
        params.append(payment_method)
    if search:
        q = f"%{search.lower()}%"
        sql += """ AND (
            CAST(t.transaction_id AS TEXT) LIKE ?
            OR LOWER(u.username) LIKE ?
            OR LOWER(u.full_name) LIKE ?
            OR LOWER(t.payment_method) LIKE ?
            OR EXISTS (
                SELECT 1 FROM transaction_items ti
                JOIN products p ON ti.product_id = p.product_id
                WHERE ti.transaction_id = t.transaction_id
                  AND LOWER(p.name) LIKE ?
            )
        )"""
        params.extend([q, q, q, q, q])

    sql += " ORDER BY t.created_at DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def get_sales_summary(date_from=None, date_to=None):
    """
    Return totals for a date range:
      - total_sales, count
      - cash_total, gcash_total
    """
    conn = get_connection()
    sql = """
        SELECT
            COALESCE(SUM(total), 0) AS total_sales,
            COUNT(*) AS count,
            COALESCE(SUM(CASE WHEN payment_method='Cash'
                              THEN total ELSE 0 END), 0) AS cash_total,
            COALESCE(SUM(CASE WHEN payment_method='GCash'
                              THEN total ELSE 0 END), 0) AS gcash_total
        FROM transactions
        WHERE 1=1
    """
    params = []
    if date_from:
        sql += " AND DATE(created_at) >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND DATE(created_at) <= ?"
        params.append(date_to)

    row = conn.execute(sql, params).fetchone()
    conn.close()
    return row


# ─────────────────────────────────────────────
# READ — ITEMS SUMMARY (for report list)
# ─────────────────────────────────────────────

def get_items_summary_for_transaction(transaction_id):
    """
    Return a compact 'Name ×Qty @ ₱Price' string for a transaction.
    Example: 'Coke ×2 @ ₱85.00, Piattos ×1 @ ₱25.00'
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT ti.quantity, ti.price, p.name
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.product_id
        WHERE ti.transaction_id = ?
        ORDER BY ti.item_id
    """, (transaction_id,)).fetchall()
    conn.close()

    if not rows:
        return "—"

    parts = [f"{r['name']} ×{r['quantity']} @ ₱{r['price']:.2f}"
             for r in rows]
    return ", ".join(parts)

# ─────────────────────────────────────────────
# DASHBOARD QUERIES
# ─────────────────────────────────────────────

def get_dashboard_stats(date_str=None):
    """
    Return a dict of key metrics for the dashboard:
      - total_sales_today, txn_count_today
      - cash_today, gcash_today
      - total_sales_alltime, txn_count_alltime
    """
    if date_str is None:
        date_str = now_local()[:10]

    conn = get_connection()

    # ---- Today's numbers ----
    today_row = conn.execute("""
        SELECT
            COALESCE(SUM(total), 0) AS sales,
            COUNT(*) AS count,
            COALESCE(SUM(CASE WHEN payment_method='Cash'
                              THEN total ELSE 0 END), 0) AS cash,
            COALESCE(SUM(CASE WHEN payment_method='GCash'
                              THEN total ELSE 0 END), 0) AS gcash
        FROM transactions
        WHERE DATE(created_at) = ?
    """, (date_str,)).fetchone()

    # ---- All-time numbers ----
    alltime_row = conn.execute("""
        SELECT
            COALESCE(SUM(total), 0) AS sales,
            COUNT(*) AS count
        FROM transactions
    """).fetchone()

    conn.close()

    return {
        "total_sales_today":   today_row["sales"],
        "txn_count_today":     today_row["count"],
        "cash_today":          today_row["cash"],
        "gcash_today":         today_row["gcash"],
        "total_sales_alltime": alltime_row["sales"],
        "txn_count_alltime":   alltime_row["count"],
    }