# ─────────────────────────────────────────────
# DATABASE SETUP (SQLite — batch-tracked inventory)
# ─────────────────────────────────────────────

import sqlite3
import datetime
from config import DB_PATH, ROLE_ADMIN


# ─────────────────────────────────────────────
# LOCAL TIME HELPER
# ─────────────────────────────────────────────

def now_local():
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
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
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
            user_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT UNIQUE NOT NULL,
            password     TEXT NOT NULL,
            first_name   TEXT NOT NULL,
            middle_name  TEXT,
            last_name    TEXT NOT NULL,
            role         TEXT NOT NULL CHECK(role IN ('admin','staff')),
            is_active    INTEGER DEFAULT 1,
            created_at   TEXT NOT NULL
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
            supplier_category_id INTEGER NOT NULL,
            contact_number       TEXT,
            contact_person_first TEXT,
            contact_person_middle TEXT,
            contact_person_last  TEXT,
            address              TEXT,
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

    # ---- 5. products ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code    TEXT UNIQUE NOT NULL,
            name            TEXT NOT NULL,
            brand           TEXT,
            size            TEXT,
            unit            TEXT DEFAULT 'pc',
            cost_price      REAL DEFAULT 0,
            price           REAL NOT NULL,
            low_stock_level INTEGER DEFAULT 10,
            image_path      TEXT,
            is_archived     INTEGER DEFAULT 0,
            supplier_id     INTEGER NOT NULL,
            category_id     INTEGER NOT NULL,
            created_at      TEXT NOT NULL,
            updated_at      TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)

    # ---- 6. batches ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            batch_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id      INTEGER NOT NULL,
            batch_no        TEXT NOT NULL,
            quantity        INTEGER NOT NULL DEFAULT 0,
            cost_price      REAL DEFAULT 0,
            expiration_date TEXT,
            supplier_id     INTEGER,
            purchase_id     INTEGER,
            is_archived     INTEGER DEFAULT 0,
            received_at     TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (product_id)  REFERENCES products(product_id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
            FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id)
        )
    """)

    # ---- 7. transactions ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            total            REAL NOT NULL,
            payment_method   TEXT NOT NULL CHECK(payment_method IN ('Cash','GCash')),
            amount_paid      REAL NOT NULL,
            change_due       REAL DEFAULT 0,
            gcash_reference  TEXT,
            created_at       TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # ---- 8. transaction_items ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transaction_items (
            item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id  INTEGER NOT NULL,
            product_id      INTEGER NOT NULL,
            batch_id        INTEGER,
            quantity        INTEGER NOT NULL,
            price           REAL NOT NULL,
            cost_price      REAL DEFAULT 0,
            subtotal        REAL NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
            FOREIGN KEY (product_id)     REFERENCES products(product_id),
            FOREIGN KEY (batch_id)       REFERENCES batches(batch_id)
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
            pitem_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id     INTEGER NOT NULL,
            product_id      INTEGER NOT NULL,
            quantity        INTEGER NOT NULL,
            cost            REAL NOT NULL,
            expiration_date TEXT,
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

    # ---- 12. Indexes (performance) ----
    _create_indexes(cur)

    conn.commit()
    conn.close()

    _run_migrations()
    _seed_default_admin()
    _seed_default_supplier_category()


# ─────────────────────────────────────────────
# INDEXES
# ─────────────────────────────────────────────

def _create_indexes(cur):
    """Create indexes that speed up dashboard + reports + POS queries."""
    index_sql = [
        # ---- batches ----
        "CREATE INDEX IF NOT EXISTS idx_batches_product ON batches(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_batches_expiration ON batches(expiration_date)",
        "CREATE INDEX IF NOT EXISTS idx_batches_archived ON batches(is_archived)",
        "CREATE INDEX IF NOT EXISTS idx_batches_product_active ON batches(product_id, is_archived, expiration_date)",

        # ---- products ----
        "CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id)",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
        "CREATE INDEX IF NOT EXISTS idx_products_archived ON products(is_archived)",

        # ---- transactions ----
        "CREATE INDEX IF NOT EXISTS idx_transactions_created ON transactions(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)",

        # ---- transaction_items ----
        "CREATE INDEX IF NOT EXISTS idx_txn_items_transaction ON transaction_items(transaction_id)",
        "CREATE INDEX IF NOT EXISTS idx_txn_items_product ON transaction_items(product_id)",

        # ---- suppliers / categories ----
        "CREATE INDEX IF NOT EXISTS idx_suppliers_category ON suppliers(supplier_category_id)",
        "CREATE INDEX IF NOT EXISTS idx_suppliers_archived ON suppliers(is_archived)",

        # ---- purchases ----
        "CREATE INDEX IF NOT EXISTS idx_purchases_supplier ON purchases(supplier_id)",
        "CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status)",
        "CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase ON purchase_items(purchase_id)",

        # ---- activity_logs ----
        "CREATE INDEX IF NOT EXISTS idx_logs_created ON activity_logs(created_at)",
    ]
    for sql in index_sql:
        try:
            cur.execute(sql)
        except sqlite3.OperationalError:
            pass


# ─────────────────────────────────────────────
# MIGRATIONS (safe ALTER TABLE — for existing DBs)
# ─────────────────────────────────────────────

def _run_migrations():
    conn = get_connection()
    cur = conn.cursor()

    # ---- suppliers: contact → contact_number + contact person ----
    migrations = [
        ("ALTER TABLE suppliers ADD COLUMN contact_number TEXT",
         "suppliers.contact_number"),
        ("ALTER TABLE suppliers ADD COLUMN contact_person_first TEXT",
         "suppliers.contact_person_first"),
        ("ALTER TABLE suppliers ADD COLUMN contact_person_middle TEXT",
         "suppliers.contact_person_middle"),
        ("ALTER TABLE suppliers ADD COLUMN contact_person_last TEXT",
         "suppliers.contact_person_last"),
    ]
    for sql, name in migrations:
        try:
            cur.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # ---- Copy old `contact` → `contact_number` (one-time) ----
    try:
        cols = [r[1] for r in cur.execute("PRAGMA table_info(suppliers)")]
        if "contact" in cols:
            cur.execute("""
                UPDATE suppliers
                SET contact_number = contact
                WHERE contact_number IS NULL
                  AND contact IS NOT NULL
                  AND contact != ''
            """)
            conn.commit()
    except Exception:
        pass

    # ---- Ensure indexes exist on pre-existing DBs ----
    _create_indexes(cur)
    conn.commit()

    conn.close()


# ─────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────

def _seed_default_admin():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM users")
        if cur.fetchone()["c"] == 0:
            cur.execute("""
                INSERT INTO users
                    (username, password, first_name, middle_name, last_name,
                     role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("admin", "admin123", "Store", None, "Owner",
                  ROLE_ADMIN, now_local()))
            conn.commit()
            print("[DB] Default admin created -> username: admin | password: admin123")
    finally:
        conn.close()


def _seed_default_supplier_category():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM supplier_categories")
        if cur.fetchone()["c"] == 0:
            cur.execute("""
                INSERT INTO supplier_categories (name, description, created_at)
                VALUES (?, ?, ?)
            """, ("General", "Default supplier category", now_local()))
            conn.commit()
            print("[DB] Default supplier category created: General")
    finally:
        conn.close()