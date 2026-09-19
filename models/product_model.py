# ─────────────────────────────────────────────
# PRODUCT MODEL
# ─────────────────────────────────────────────

from database import get_connection, now_local


# ─────────────────────────────────────────────
# PRODUCT CODE GENERATOR
# ─────────────────────────────────────────────

def _generate_product_code(cur):
    """Generate the next code like PRD-0001, PRD-0002, ..."""
    cur.execute("SELECT COUNT(*) AS c FROM products")
    count = cur.fetchone()["c"] + 1
    return f"PRD-{count:04d}"


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
    return rows


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
    return rows


def get_product(product_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM products WHERE product_id = ?",
        (product_id,)
    ).fetchone()
    conn.close()
    return row


def get_low_stock_products():
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*,
               s.name AS supplier_name,
               c.name AS category_name
        FROM products p
        JOIN suppliers  s ON p.supplier_id = s.supplier_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.stock_qty <= p.low_stock_level
          AND p.is_archived = 0
        ORDER BY p.stock_qty
    """).fetchall()
    conn.close()
    return rows


def get_products_by_supplier(supplier_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*,
               s.name AS supplier_name,
               c.name AS category_name
        FROM products p
        JOIN suppliers  s ON p.supplier_id = s.supplier_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.supplier_id = ?
          AND p.is_archived = 0
        ORDER BY p.name
    """, (supplier_id,)).fetchall()
    conn.close()
    return rows


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def add_product(name, price, stock_qty, low_stock_level,
                supplier_id, category_id, image_path=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        code = _generate_product_code(cur)

        cur.execute("""
            INSERT INTO products
                (product_code, name, price, stock_qty, low_stock_level,
                 supplier_id, category_id, image_path, is_archived, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """, (code, name, price, stock_qty, low_stock_level,
              supplier_id, category_id, image_path, now_local()))
        conn.commit()
        return True, f"Product added ({code})."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_product(product_id, name, price, stock_qty, low_stock_level,
                   supplier_id, category_id, image_path=None):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE products
            SET name = ?, price = ?, stock_qty = ?, low_stock_level = ?,
                supplier_id = ?, category_id = ?, image_path = ?
            WHERE product_id = ?
        """, (name, price, stock_qty, low_stock_level,
              supplier_id, category_id, image_path, product_id))
        conn.commit()
        return True, "Product updated."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def restock_product(product_id, quantity):
    """Add quantity to existing stock."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE products
            SET stock_qty = stock_qty + ?
            WHERE product_id = ?
        """, (quantity, product_id))
        conn.commit()
        return True, f"Restocked +{quantity}."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def archive_product(product_id):
    """Soft-delete: mark as archived."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE products SET is_archived = 1 WHERE product_id = ?",
            (product_id,)
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
            "UPDATE products SET is_archived = 0 WHERE product_id = ?",
            (product_id,)
        )
        conn.commit()
        return True, "Product restored."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# STOCK ADJUSTERS (kept from before)
# ─────────────────────────────────────────────

def deduct_stock(product_id, qty):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE products SET stock_qty = stock_qty - ? WHERE product_id = ?",
            (qty, product_id)
        )
        conn.commit()
    finally:
        conn.close()


def add_stock(product_id, qty):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE products SET stock_qty = stock_qty + ? WHERE product_id = ?",
            (qty, product_id)
        )
        conn.commit()
    finally:
        conn.close()


def deduct_stock_cur(cur, product_id, qty):
    cur.execute(
        "UPDATE products SET stock_qty = stock_qty - ? WHERE product_id = ?",
        (qty, product_id)
    )


def add_stock_cur(cur, product_id, qty):
    cur.execute(
        "UPDATE products SET stock_qty = stock_qty + ? WHERE product_id = ?",
        (qty, product_id)
    )

# ─────────────────────────────────────────────
# DASHBOARD HELPERS
# ─────────────────────────────────────────────

def get_product_counts():
    """
    Return:
      - total_products (non-archived)
      - low_stock_count
      - out_of_stock_count
    """
    conn = get_connection()

    total = conn.execute("""
        SELECT COUNT(*) AS c FROM products WHERE is_archived = 0
    """).fetchone()["c"]

    low = conn.execute("""
        SELECT COUNT(*) AS c FROM products
        WHERE is_archived = 0 AND stock_qty > 0
          AND stock_qty <= low_stock_level
    """).fetchone()["c"]

    out = conn.execute("""
        SELECT COUNT(*) AS c FROM products
        WHERE is_archived = 0 AND stock_qty <= 0
    """).fetchone()["c"]

    conn.close()

    return {
        "total_products":     total,
        "low_stock_count":    low,
        "out_of_stock_count": out,
    }