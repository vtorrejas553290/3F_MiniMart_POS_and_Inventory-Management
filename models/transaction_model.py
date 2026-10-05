# ─────────────────────────────────────────────
# TRANSACTION MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local
from models.batch_model import deduct_fefo_cur


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _full_name_sql(alias="u"):
    """
    Return a SQL fragment that builds a display name from
    first_name / middle_name / last_name, matching
    user_model._build_full_name() behavior.
    """
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

def create_transaction(user_id, cart, payment_method, amount_paid,
                       gcash_reference=None):
    total = sum(item["price"] * item["quantity"] for item in cart)

    if payment_method == "Cash" and amount_paid < total:
        return False, "Insufficient payment.", 0

    change = amount_paid - total if payment_method == "Cash" else 0

    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO transactions
                (user_id, total, payment_method, amount_paid,
                 change_due, gcash_reference, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, total, payment_method, amount_paid,
              change, gcash_reference, now_local()))
        txn_id = cur.lastrowid

        for item in cart:
            ok, msg, _cost = deduct_fefo_cur(
                cur,
                product_id=item["product_id"],
                quantity=item["quantity"],
                transaction_id=txn_id,
            )
            if not ok:
                conn.rollback()
                return False, f"{item['name']}: {msg}", 0

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
    rows = conn.execute(f"""
        SELECT t.*, u.username, {_full_name_sql('u')}
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
# READ — FILTERED
# ─────────────────────────────────────────────

def get_transactions_filtered(date_from=None, date_to=None,
                              search=None, payment_method=None):
    conn = get_connection()
    sql = f"""
        SELECT t.*,
               u.username, {_full_name_sql('u')},
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
            OR LOWER(COALESCE(u.first_name,'') || ' ' ||
                     COALESCE(u.middle_name,'') || ' ' ||
                     COALESCE(u.last_name,'')) LIKE ?
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
# READ — ITEMS SUMMARY
# ─────────────────────────────────────────────

def get_items_summary_for_transaction(transaction_id):
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
# DASHBOARD
# ─────────────────────────────────────────────

def get_dashboard_stats(date_str=None):
    if date_str is None:
        date_str = now_local()[:10]

    conn = get_connection()

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


# ─────────────────────────────────────────────
# TOP SELLING PRODUCTS
# ─────────────────────────────────────────────

def get_top_selling_products(date_from=None, date_to=None,
                             search=None, payment_method=None, limit=5):
    conn = get_connection()
    sql = """
        SELECT
            p.name            AS product_name,
            p.brand           AS brand,
            p.size            AS size,
            p.product_code    AS product_code,
            COALESCE(SUM(ti.quantity), 0)                 AS units_sold,
            COUNT(DISTINCT ti.transaction_id)             AS transaction_count,
            COALESCE(SUM(ti.subtotal), 0)                 AS revenue,
            COALESCE(SUM(ti.cost_price * ti.quantity), 0) AS total_cost
        FROM transaction_items ti
        JOIN products     p ON ti.product_id     = p.product_id
        JOIN transactions t ON ti.transaction_id = t.transaction_id
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
        sql += " AND LOWER(p.name) LIKE ?"
        params.append(q)

    sql += """
        GROUP BY p.product_id, p.name, p.brand, p.size, p.product_code
        ORDER BY units_sold DESC
        LIMIT ?
    """
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    # ---- Compute averages + profit in Python ----
    result = []
    for r in rows:
        d = dict(r)
        units = d["units_sold"] or 0
        revenue = d["revenue"] or 0
        total_cost = d["total_cost"] or 0

        if units > 0:
            d["avg_price"] = revenue / units
            d["avg_cost"]  = total_cost / units
        else:
            d["avg_price"] = 0
            d["avg_cost"]  = 0

        d["profit"] = revenue - total_cost
        result.append(d)

    return result

def get_profit_breakdown_today(date_str=None):
    """
    Return profit breakdown for a given day (default today):
      - profit         : total profit
      - revenue        : total revenue
      - cost           : total cost of goods sold
      - cash_profit    : profit from Cash transactions
      - gcash_profit   : profit from GCash transactions
      - txn_count      : number of transactions today
    """
    if date_str is None:
        date_str = now_local()[:10]

    conn = get_connection()
    row = conn.execute("""
        SELECT
            COALESCE(SUM((ti.price - ti.cost_price) * ti.quantity), 0) AS profit,
            COALESCE(SUM(ti.subtotal), 0)                              AS revenue,
            COALESCE(SUM(ti.cost_price * ti.quantity), 0)              AS cost,
            COALESCE(SUM(CASE WHEN t.payment_method = 'Cash'
                              THEN (ti.price - ti.cost_price) * ti.quantity
                              ELSE 0 END), 0)                          AS cash_profit,
            COALESCE(SUM(CASE WHEN t.payment_method = 'GCash'
                              THEN (ti.price - ti.cost_price) * ti.quantity
                              ELSE 0 END), 0)                          AS gcash_profit
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.transaction_id
        WHERE DATE(t.created_at) = ?
    """, (date_str,)).fetchone()

    txn_count = conn.execute("""
        SELECT COUNT(*) AS c FROM transactions
        WHERE DATE(created_at) = ?
    """, (date_str,)).fetchone()["c"]

    conn.close()

    return {
        "profit":       row["profit"],
        "revenue":      row["revenue"],
        "cost":         row["cost"],
        "cash_profit":  row["cash_profit"],
        "gcash_profit": row["gcash_profit"],
        "txn_count":    txn_count,
    }