# ─────────────────────────────────────────────
# PRODUCT MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local
from models.batch_model import (
    create_batch_cur, get_total_stock, get_earliest_expiration,
)


# ─────────────────────────────────────────────
# PRODUCT CODE GENERATOR
# ─────────────────────────────────────────────

def _generate_product_code(cur):
    cur.execute("SELECT COUNT(*) AS c FROM products")
    count = cur.fetchone()["c"] + 1
    return f"PRD-{count:04d}"


# ─────────────────────────────────────────────
# STOCK AGGREGATION HELPERS
# ─────────────────────────────────────────────

def _attach_stock(rows):
    """
    Given a list of product rows, add `stock_qty` and `earliest_expiration`
    keys by aggregating from the batches table.
    Returns the same list of dicts (sqlite3.Row isn't mutable).
    """
    if not rows:
        return []

    result = []
    today = now_local()[:10]

    conn = get_connection()
    for row in rows:
        d = dict(row)

        # ---- Sum non-expired quantity ----
        agg = conn.execute("""
            SELECT
                COALESCE(SUM(quantity), 0) AS stock_qty
            FROM batches
            WHERE product_id = ?
              AND is_archived = 0
              AND (expiration_date IS NULL OR expiration_date >= ?)
        """, (d["product_id"], today)).fetchone()

        # ---- Earliest non-expired expiration ----
        earliest = conn.execute("""
            SELECT MIN(expiration_date) AS earliest
            FROM batches
            WHERE product_id = ?
              AND is_archived = 0
              AND quantity > 0
              AND expiration_date IS NOT NULL
              AND expiration_date >= ?
        """, (d["product_id"], today)).fetchone()

        d["stock_qty"] = agg["stock_qty"]
        d["earliest_expiration"] = earliest["earliest"] if earliest else None
        result.append(d)

    conn.close()
    return result


# ─────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────

def get_all_products(include_archived=False):
    conn = get_connection()
    sql = """
        SELECT p.*,
               s.name AS supplier_name,
               c.name AS category_name
        FROM products p
        JOIN suppliers  s ON p.supplier_id = s.supplier_id
        JOIN categories c ON p.category_id = c.category_id
    """
    if not include_archived:
        sql += " WHERE p.is_archived = 0"
    sql += " ORDER BY c.name, p.name"

    rows = conn.execute(sql).fetchall()
    conn.close()
    return _attach_stock(rows)


def get_products_by_category(category_id, include_archived=False):
    conn = get_connection()
    sql = """
        SELECT p.*,
               s.name AS supplier_name,
               c.name AS category_name
        FROM products p
        JOIN suppliers  s ON p.supplier_id = s.supplier_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE 1=1
    """
    params = []
    if category_id:
        sql += " AND p.category_id = ?"
        params.append(category_id)
    if not include_archived:
        sql += " AND p.is_archived = 0"
    sql += " ORDER BY p.name"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return _attach_stock(rows)


def get_product(product_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT p.*,
               s.name AS supplier_name,
               c.name AS category_name
        FROM products p
        JOIN suppliers  s ON p.supplier_id = s.supplier_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.product_id = ?
    """, (product_id,)).fetchone()
    conn.close()

    if row is None:
        return None
    return _attach_stock([row])[0]


def get_low_stock_products():
    """
    Products whose total non-expired stock is <= low_stock_level.
    """
    all_products = get_all_products(include_archived=False)
    return [
        p for p in all_products
        if p["stock_qty"] <= (p["low_stock_level"] or 0)
    ]


def get_products_by_supplier(supplier_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*,
               s.name AS supplier_name,
               c.name AS category_name
        FROM products p
        JOIN suppliers  s ON p.supplier_id = s.supplier_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.supplier_id = ? AND p.is_archived = 0
        ORDER BY p.name
    """, (supplier_id,)).fetchall()
    conn.close()
    return _attach_stock(rows)


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def add_product(name, price, stock_qty, low_stock_level,
                supplier_id, category_id, image_path=None,
                brand=None, size=None, unit="pc", cost_price=0.0,
                expiration_date=None):
    """
    Create a product AND an initial batch for its starting stock.

    Stock is never stored on products — it lives in `batches`.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        code = _generate_product_code(cur)
        now = now_local()

        # ---- Insert product ----
        cur.execute("""
            INSERT INTO products
                (product_code, name, brand, size, unit, cost_price, price,
                 low_stock_level, supplier_id, category_id, image_path,
                 is_archived, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (code, name, brand, size, unit, cost_price, price,
              low_stock_level, supplier_id, category_id, image_path,
              now, now))
        product_id = cur.lastrowid

        # ---- Create the initial batch (if any stock was given) ----
        if stock_qty and stock_qty > 0:
            create_batch_cur(
                cur,
                product_id=product_id,
                quantity=stock_qty,
                cost_price=cost_price or 0,
                expiration_date=expiration_date or None,
                supplier_id=supplier_id,
                purchase_id=None,
            )

        conn.commit()
        return True, f"Product added ({code})."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_product(product_id, name, price, low_stock_level,
                   supplier_id, category_id, image_path=None,
                   brand=None, size=None, unit="pc", cost_price=0.0):
    """
    Update product info only. Stock lives in batches and is NOT touched here.
    Use create_batch() to add stock, or RestockDialog.
    """
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE products
            SET name = ?, brand = ?, size = ?, unit = ?, cost_price = ?,
                price = ?, low_stock_level = ?,
                supplier_id = ?, category_id = ?, image_path = ?,
                updated_at = ?
            WHERE product_id = ?
        """, (name, brand, size, unit, cost_price,
              price, low_stock_level,
              supplier_id, category_id, image_path,
              now_local(), product_id))
        conn.commit()
        return True, "Product updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def restock_product(product_id, quantity, cost_price=None,
                    expiration_date=None, supplier_id=None):
    """
    Add stock by creating a NEW batch.
    Cost defaults to the product's current cost_price if not given.
    """
    if quantity <= 0:
        return False, "Quantity must be positive."

    conn = get_connection()
    try:
        cur = conn.cursor()

        # ---- Default cost from product if not provided ----
        if cost_price is None:
            row = cur.execute(
                "SELECT cost_price, supplier_id FROM products WHERE product_id = ?",
                (product_id,)
            ).fetchone()
            cost_price = row["cost_price"] if row else 0
            if supplier_id is None:
                supplier_id = row["supplier_id"] if row else None

        create_batch_cur(
            cur,
            product_id=product_id,
            quantity=quantity,
            cost_price=cost_price or 0,
            expiration_date=expiration_date or None,
            supplier_id=supplier_id,
            purchase_id=None,
        )

        conn.commit()
        return True, f"Restocked +{quantity}."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_cost_price(product_id, cost_price):
    """Standalone cost update (products.cost_price — used as a default)."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE products
            SET cost_price = ?, updated_at = ?
            WHERE product_id = ?
        """, (cost_price, now_local(), product_id))
        conn.commit()
        return True, "Cost price updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def archive_product(product_id):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE products SET is_archived = 1, updated_at = ? "
            "WHERE product_id = ?",
            (now_local(), product_id)
        )
        conn.commit()
        return True, "Product archived."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def unarchive_product(product_id):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE products SET is_archived = 0, updated_at = ? "
            "WHERE product_id = ?",
            (now_local(), product_id)
        )
        conn.commit()
        return True, "Product restored."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# DASHBOARD HELPERS
# ─────────────────────────────────────────────

def get_product_counts():
    """
    Return:
      - total_products (non-archived)
      - low_stock_count
      - out_of_stock_count
    Uses batch aggregation.
    """
    products = get_all_products(include_archived=False)

    total = len(products)
    low = sum(
        1 for p in products
        if p["stock_qty"] > 0 and p["stock_qty"] <= (p["low_stock_level"] or 0)
    )
    out = sum(1 for p in products if p["stock_qty"] <= 0)

    return {
        "total_products":     total,
        "low_stock_count":    low,
        "out_of_stock_count": out,
    }