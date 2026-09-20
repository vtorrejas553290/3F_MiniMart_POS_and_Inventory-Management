# ─────────────────────────────────────────────
# DATABASE SETUP (SQLite — strict one-to-many)
# ─────────────────────────────────────────────
#
# Relationship map (no many-to-many, no hanging tables):
#
#   users ──< transactions ──< transaction_items >── products
#   users ──< purchases    ──< purchase_items    >── products
#   users ──< activity_logs
#   supplier_categories ──< suppliers ──< products
#   categories          ──< products
#   products            ──< inventory          ← NEW
#
# Root tables: users, categories, supplier_categories

import sqlite3
import datetime
from config import DB_PATH, ROLE_ADMIN


# ─────────────────────────────────────────────
# LOCAL TIME HELPER
# ─────────────────────────────────────────────

def now_local():
    """Return current local time as 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


# ─────────────────────────────────────────────
# INITIALIZATION
# ─────────────────────────────────────────────

def initialize_database():
    conn = get_connection()
    cur = conn.cursor()

    # ---- 1. users ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            full_name   TEXT NOT NULL,
            role        TEXT NOT NULL CHECK(role IN ('admin','staff')),
            is_active   INTEGER DEFAULT 1,
            created_at  TEXT NOT NULL
        )
    """)

    # ---- 2. supplier_categories ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS supplier_categories (
            scat_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at  TEXT NOT NULL
        )
    """)

    # ---- 3. suppliers ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name                 TEXT NOT NULL,
            contact              TEXT,
            address              TEXT,
            supplier_category_id INTEGER NOT NULL,
            is_archived          INTEGER DEFAULT 0,
            created_at           TEXT NOT NULL,
            FOREIGN KEY (supplier_category_id)
                REFERENCES supplier_categories(scat_id)
        )
    """)

    # ---- 4. categories ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at  TEXT NOT NULL
        )
    """)

    # ---- 5. products (NO stock_qty — moved to inventory) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code    TEXT UNIQUE NOT NULL,
            name            TEXT NOT NULL,
            price           REAL NOT NULL,
            low_stock_level INTEGER DEFAULT 10,
            image_path      TEXT,
            is_archived     INTEGER DEFAULT 0,
            supplier_id     INTEGER NOT NULL,
            category_id     INTEGER NOT NULL,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)

    # ---- 6. inventory (child of products, one-to-many) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id   INTEGER NOT NULL,
            stock_qty    INTEGER NOT NULL DEFAULT 0,
            updated_at   TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # ---- 7. transactions ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            total           REAL NOT NULL,
            payment_method  TEXT NOT NULL CHECK(payment_method IN ('Cash','GCash')),
            amount_paid     REAL NOT NULL,
            change_due      REAL DEFAULT 0,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # ---- 8. transaction_items ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transaction_items (
            item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id  INTEGER NOT NULL,
            product_id      INTEGER NOT NULL,
            quantity        INTEGER NOT NULL,
            price           REAL NOT NULL,
            subtotal        REAL NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
            FOREIGN KEY (product_id)     REFERENCES products(product_id)
        )
    """)

    # ---- 9. purchases ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id  INTEGER NOT NULL,
            user_id      INTEGER NOT NULL,
            total_cost   REAL DEFAULT 0,
            status       TEXT NOT NULL DEFAULT 'Ordered'
                         CHECK(status IN ('Ordered','Received','Cancelled')),
            notes        TEXT,
            created_at   TEXT NOT NULL,
            received_at  TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
            FOREIGN KEY (user_id)     REFERENCES users(user_id)
        )
    """)

    # ---- 10. purchase_items ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (
            pitem_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id  INTEGER NOT NULL,
            product_id   INTEGER NOT NULL,
            quantity     INTEGER NOT NULL,
            cost         REAL NOT NULL,
            FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id),
            FOREIGN KEY (product_id)  REFERENCES products(product_id)
        )
    """)

    # ---- 11. activity_logs ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            action      TEXT NOT NULL,
            details     TEXT,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()

    _run_migrations(cur, conn)
    _seed_default_admin(cur, conn)
    _seed_default_supplier_category(cur, conn)

    conn.close()


# ─────────────────────────────────────────────
# MIGRATIONS
# ─────────────────────────────────────────────

def _run_migrations(cur, conn):
    """Add new columns to existing DBs without data loss."""
    migrations = [
        # ---- suppliers ----
        ("ALTER TABLE suppliers ADD COLUMN supplier_category_id INTEGER",
         "suppliers.supplier_category_id"),
        ("ALTER TABLE suppliers ADD COLUMN is_archived INTEGER DEFAULT 0",
         "suppliers.is_archived"),

        # ---- products ----
        ("ALTER TABLE products ADD COLUMN product_code TEXT",
         "products.product_code"),
        ("ALTER TABLE products ADD COLUMN image_path TEXT",
         "products.image_path"),
        ("ALTER TABLE products ADD COLUMN is_archived INTEGER DEFAULT 0",
         "products.is_archived"),

        # ---- purchases ----
        ("ALTER TABLE purchases ADD COLUMN status TEXT DEFAULT 'Ordered'",
         "purchases.status"),
        ("ALTER TABLE purchases ADD COLUMN notes TEXT",
         "purchases.notes"),
        ("ALTER TABLE purchases ADD COLUMN received_at TEXT",
         "purchases.received_at"),
    ]
    for sql, name in migrations:
        try:
            cur.execute(sql)
            conn.commit()
            print(f"[DB] Migration applied: {name}")
        except sqlite3.OperationalError:
            pass

    # ═════════════════════════════════════════
    # MIGRATE products.stock_qty → inventory
    # ═════════════════════════════════════════
    try:
        cols = [r[1] for r in cur.execute("PRAGMA table_info(products)")]
        if "stock_qty" in cols:
            # ---- Copy each product's stock into a new inventory row ----
            # Only insert if the product doesn't already have an inventory row.
            cur.execute("""
                INSERT INTO inventory (product_id, stock_qty, updated_at)
                SELECT p.product_id,
                       COALESCE(p.stock_qty, 0),
                       ?
                FROM products p
                WHERE p.product_id NOT IN (
                    SELECT product_id FROM inventory
                )
            """, (now_local(),))
            conn.commit()
            print("[DB] Migrated products.stock_qty → inventory table")
    except Exception as e:
        print(f"[DB] Migration note: {e}")


# ─────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────

def _seed_default_admin(cur, conn):
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        cur.execute("""
            INSERT INTO users (username, password, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin123", "Store Owner", ROLE_ADMIN, now_local()))
        conn.commit()
        print("[DB] Default admin created -> username: admin | password: admin123")


def _seed_default_supplier_category(cur, conn):
    cur.execute("SELECT COUNT(*) AS c FROM supplier_categories")
    if cur.fetchone()["c"] == 0:
        cur.execute("""
            INSERT INTO supplier_categories (name, description, created_at)
            VALUES (?, ?, ?)
        """, ("General", "Default supplier category", now_local()))
        conn.commit()
        print("[DB] Default supplier category created: General")