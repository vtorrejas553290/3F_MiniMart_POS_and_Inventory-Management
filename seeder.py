# ─────────────────────────────────────────────
# SEEDER — Filipino products, suppliers, transactions
# ─────────────────────────────────────────────
#
# Run: python seeder.py
#
# Idempotent-ish: it checks for existing data and skips inserts if a
# table is already populated, so you can run it multiple times safely.
# To reseed from scratch, run `python reset_db.py` first.

import random
import sqlite3
from datetime import datetime, timedelta

from database import get_connection, now_local
from models.product_model import add_product
from models.batch_model import create_batch
from models.transaction_model import create_transaction


# ─────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────

SUPPLIER_CATEGORIES = [
    ("Beverages",  "Soft drinks, juices, water"),
    ("Snacks",     "Chips, biscuits, candies"),
    ("Canned Goods", "Canned meats, fish, vegetables"),
    ("Noodles",    "Instant noodles and pasta"),
    ("Household",  "Cleaning and personal care"),
]

SUPPLIERS = [
    # name, supplier_category, contact_number, first, middle, last, address
    ("Coca-Cola Beverages Philippines", "Beverages", "09171234567",
     "Juan", "Santos", "Dela Cruz", "BGC, Taguig City"),
    ("Pepsi-Cola Products Philippines", "Beverages", "09172345678",
     "Maria", None, "Reyes", "Muntinlupa City"),
    ("Jack 'n Jill (URC)", "Snacks", "09173456789",
     "Antonio", "Go", "Tan", "Pasig City"),
    ("M.Y. San (Rebisco)", "Snacks", "09174567890",
     "Carlos", "Lim", "Chan", "Quezon City"),
    ("Century Pacific Food Inc.", "Canned Goods", "09175678901",
     "Ramon", "Co", "Sy", "Pasig City"),
    ("Universal Robina Corp. (URC)", "Noodles", "09176789012",
     "Lance", "Yu", "Gokongwei", "Ortigas Center, Pasig"),
    ("Monde Nissin Corporation", "Noodles", "09177890123",
     "Betty", None, "Ang", "Sta. Rosa, Laguna"),
    ("San Miguel Foods Inc.", "Canned Goods", "09178901234",
     "Ferdinand", "Cruz", "Marcos", "Mandaluyong City"),
    ("Procter & Gamble Philippines", "Household", "09179012345",
     "Robert", None, "McDonald", "Taguig City"),
    ("Unilever Philippines", "Household", "09180123456",
     "Andres", "Bonifacio", "Rizal", "BGC, Taguig"),
]

CATEGORIES = [
    ("Beverages",    "Soft drinks, juices, water"),
    ("Snacks",       "Chips, biscuits, candies"),
    ("Canned Goods", "Canned meats, fish"),
    ("Noodles",      "Instant noodles"),
    ("Household",    "Cleaning and personal care"),
]

# product_code, name, brand, size, unit, cost, price, low, supplier_name, category_name, expiry
PRODUCTS = [
    # ---- Beverages ----
    ("Coke Mismo",        "Coca-Cola",       "300ml", "pc", 10.00, 18.00, 12, "Coca-Cola Beverages Philippines", "Beverages", "2027-06-30"),
    ("Coke Regular",      "Coca-Cola",       "500ml", "pc", 15.00, 25.00, 10, "Coca-Cola Beverages Philippines", "Beverages", "2027-06-30"),
    ("Coke 1.5L",         "Coca-Cola",       "1.5L",  "pc", 45.00, 70.00,  5, "Coca-Cola Beverages Philippines", "Beverages", "2027-06-30"),
    ("Sprite Mismo",      "Sprite",          "300ml", "pc", 10.00, 18.00, 12, "Coca-Cola Beverages Philippines", "Beverages", "2027-04-15"),
    ("Royal Mismo",       "Royal",           "300ml", "pc", 10.00, 18.00, 12, "Coca-Cola Beverages Philippines", "Beverages", "2027-04-15"),
    ("Pepsi Regular",     "Pepsi",           "500ml", "pc", 14.00, 22.00, 10, "Pepsi-Cola Products Philippines", "Beverages", "2027-03-01"),
    ("Mountain Dew",      "Mountain Dew",    "500ml", "pc", 15.00, 24.00,  8, "Pepsi-Cola Products Philippines", "Beverages", "2027-02-20"),
    ("Wilkins Distilled", "Wilkins",         "500ml", "pc",  8.00, 15.00, 20, "Coca-Cola Beverages Philippines", "Beverages", None),

    # ---- Snacks ----
    ("Piattos Cheese",    "Jack 'n Jill",    "40g",   "pc", 12.00, 22.00, 15, "Jack 'n Jill (URC)", "Snacks", "2027-01-15"),
    ("Piattos Sour Cream","Jack 'n Jill",    "40g",   "pc", 12.00, 22.00, 15, "Jack 'n Jill (URC)", "Snacks", "2027-01-15"),
    ("Nova Multigrain",   "Jack 'n Jill",    "40g",   "pc", 12.00, 22.00, 15, "Jack 'n Jill (URC)", "Snacks", "2027-02-01"),
    ("Chippy BBQ",        "Jack 'n Jill",    "110g",  "pc", 18.00, 30.00, 10, "Jack 'n Jill (URC)", "Snacks", "2027-01-20"),
    ("Roller Coaster",    "Jack 'n Jill",    "80g",   "pc", 14.00, 24.00, 12, "Jack 'n Jill (URC)", "Snacks", "2027-03-10"),
    ("Pillows Ube",       "Jack 'n Jill",    "40g",   "pc", 10.00, 18.00, 15, "Jack 'n Jill (URC)", "Snacks", "2027-01-05"),
    ("Cream-O Vanilla",   "Jack 'n Jill",    "50g",   "pc", 10.00, 18.00, 15, "Jack 'n Jill (URC)", "Snacks", "2027-02-15"),
    ("Rebisco Crackers",  "Rebisco",         "35g",   "pc",  8.00, 15.00, 20, "M.Y. San (Rebisco)", "Snacks", "2027-04-01"),
    ("SkyFlakes",         "M.Y. San",        "25g",   "pc",  7.00, 12.00, 25, "M.Y. San (Rebisco)", "Snacks", "2027-05-20"),

    # ---- Canned Goods ----
    ("555 Sardines",      "555",             "155g",  "can", 20.00, 32.00, 15, "Century Pacific Food Inc.", "Canned Goods", "2028-06-30"),
    ("Ligo Sardines",     "Ligo",            "155g",  "can", 20.00, 32.00, 15, "Century Pacific Food Inc.", "Canned Goods", "2028-06-30"),
    ("Century Tuna",      "Century",         "155g",  "can", 30.00, 45.00, 10, "Century Pacific Food Inc.", "Canned Goods", "2028-08-15"),
    ("Argentina Corned Beef", "Argentina",   "150g",  "can", 35.00, 55.00, 10, "San Miguel Foods Inc.", "Canned Goods", "2028-03-01"),
    ("Purefoods Corned Beef", "Purefoods",   "150g",  "can", 40.00, 60.00, 10, "San Miguel Foods Inc.", "Canned Goods", "2028-03-01"),

    # ---- Noodles ----
    ("Lucky Me Pancit Canton Original", "Lucky Me", "60g", "pack", 12.00, 20.00, 20, "Monde Nissin Corporation", "Noodles", "2027-09-30"),
    ("Lucky Me Pancit Canton Sweet & Spicy", "Lucky Me", "60g", "pack", 12.00, 20.00, 20, "Monde Nissin Corporation", "Noodles", "2027-09-30"),
    ("Lucky Me Beef Mami", "Lucky Me",      "55g",   "pack", 10.00, 18.00, 20, "Monde Nissin Corporation", "Noodles", "2027-07-15"),
    ("Nissin Cup Noodles Seafood", "Nissin", "40g",   "pc",   25.00, 40.00, 12, "Universal Robina Corp. (URC)", "Noodles", "2027-08-20"),
    ("Payless Xtra Big Canton", "Payless",   "60g",   "pack", 11.00, 18.00, 20, "Universal Robina Corp. (URC)", "Noodles", "2027-11-30"),

    # ---- Household ----
    ("Safeguard Pure White", "Safeguard",    "60g",   "pc", 25.00, 40.00, 15, "Procter & Gamble Philippines", "Household", "2028-12-31"),
    ("Head & Shoulders",     "H&S",          "170ml", "pc", 90.00, 140.00, 8, "Procter & Gamble Philippines", "Household", "2028-06-30"),
    ("Rexona Roll-On",       "Rexona",       "50ml",  "pc", 65.00, 100.00, 10, "Unilever Philippines", "Household", "2028-09-30"),
    ("Axe Body Spray",       "Axe",          "150ml", "pc", 120.00, 180.00, 5, "Unilever Philippines", "Household", None),
    ("Surf Powder Sachet",   "Surf",         "65g",   "pack", 8.00, 15.00, 25, "Unilever Philippines", "Household", "2028-05-15"),
]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _count(conn, table):
    return conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]


def _existing_names(conn, table, column="name"):
    return {r[column] for r in conn.execute(f"SELECT {column} FROM {table}")}


# ─────────────────────────────────────────────
# SEED
# ─────────────────────────────────────────────

def seed_all(verbose=True):
    seed_supplier_categories(verbose)
    seed_suppliers(verbose)
    seed_categories(verbose)
    seed_products(verbose)
    seed_transactions(verbose)
    if verbose:
        print("\n✅ Seed complete.")


# ---- supplier_categories ----

def seed_supplier_categories(verbose=True):
    conn = get_connection()
    try:
        existing = _existing_names(conn, "supplier_categories")
        added = 0
        for name, desc in SUPPLIER_CATEGORIES:
            if name in existing:
                continue
            conn.execute("""
                INSERT INTO supplier_categories (name, description, created_at)
                VALUES (?, ?, ?)
            """, (name, desc, now_local()))
            added += 1
        conn.commit()
        if verbose and added:
            print(f"[Seeder] Inserted {added} supplier categories.")
    finally:
        conn.close()


# ---- suppliers ----

def seed_suppliers(verbose=True):
    conn = get_connection()
    try:
        existing = _existing_names(conn, "suppliers")
        # Map supplier_category name -> scat_id
        cat_map = {r["name"]: r["scat_id"]
                   for r in conn.execute("SELECT scat_id, name FROM supplier_categories")}

        added = 0
        for (name, scat_name, contact, first, mid, last, address) in SUPPLIERS:
            if name in existing:
                continue
            scat_id = cat_map.get(scat_name)
            if scat_id is None:
                continue
            conn.execute("""
                INSERT INTO suppliers
                    (name, supplier_category_id, contact_number,
                     contact_person_first, contact_person_middle,
                     contact_person_last, address,
                     is_archived, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (name, scat_id, contact, first, mid, last, address, now_local()))
            added += 1
        conn.commit()
        if verbose and added:
            print(f"[Seeder] Inserted {added} suppliers.")
    finally:
        conn.close()


# ---- product categories ----

def seed_categories(verbose=True):
    conn = get_connection()
    try:
        existing = _existing_names(conn, "categories")
        added = 0
        for name, desc in CATEGORIES:
            if name in existing:
                continue
            conn.execute("""
                INSERT INTO categories (name, description, created_at)
                VALUES (?, ?, ?)
            """, (name, desc, now_local()))
            added += 1
        conn.commit()
        if verbose and added:
            print(f"[Seeder] Inserted {added} categories.")
    finally:
        conn.close()


# ---- products ----

def seed_products(verbose=True):
    conn = get_connection()
    try:
        existing = _existing_names(conn, "products", "name")
        sup_map = {r["name"]: r["supplier_id"]
                   for r in conn.execute("SELECT supplier_id, name FROM suppliers")}
        cat_map = {r["name"]: r["category_id"]
                   for r in conn.execute("SELECT category_id, name FROM categories")}
    finally:
        conn.close()

    added = 0
    for (name, brand, size, unit, cost, price, low,
         sup_name, cat_name, expiry) in PRODUCTS:
        if name in existing:
            continue

        sup_id = sup_map.get(sup_name)
        cat_id = cat_map.get(cat_name)
        if sup_id is None or cat_id is None:
            continue

        # ---- Random starting stock ----
        initial_stock = random.randint(30, 120)

        ok, msg = add_product(
            name=name,
            price=price,
            stock_qty=initial_stock,
            low_stock_level=low,
            supplier_id=sup_id,
            category_id=cat_id,
            brand=brand,
            size=size,
            unit=unit,
            cost_price=cost,
            expiration_date=expiry,
        )
        if ok:
            added += 1

    if verbose and added:
        print(f"[Seeder] Inserted {added} products.")


# ---- transactions ----

def seed_transactions(verbose=True, count=40):
    """
    Create `count` random sales spread over the last 14 days.

    Uses create_transaction(), which goes through FEFO deduction,
    so batches are decremented correctly and transaction_items
    get cost_price snapshots for profit reporting.
    """
    conn = get_connection()
    try:
        # Don't reseed if there's already sales history
        if _count(conn, "transactions") > 0:
            if verbose:
                print("[Seeder] Transactions already exist, skipping.")
            return

        products = conn.execute("""
            SELECT p.product_id, p.name, p.price
            FROM products p
            WHERE p.is_archived = 0
        """).fetchall()
    finally:
        conn.close()

    if not products:
        if verbose:
            print("[Seeder] No products, skipping transactions.")
        return

    # ---- Get admin user_id ----
    conn = get_connection()
    user_row = conn.execute(
        "SELECT user_id FROM users WHERE role = 'admin' LIMIT 1"
    ).fetchone()
    conn.close()

    if not user_row:
        if verbose:
            print("[Seeder] No admin user, skipping transactions.")
        return

    user_id = user_row["user_id"]

    today = datetime.now()
    added = 0

    for i in range(count):
        # ---- Random date in the last 14 days ----
        days_ago = random.randint(0, 13)
        hours_ago = random.randint(8, 20)
        sale_dt = today - timedelta(days=days_ago)
        # (create_transaction always uses now_local() so the DB timestamps
        #  will be today's real time — the historical spread here is
        #  a limitation of the seeder, not the schema.)

        # ---- Pick 1 to 4 distinct products ----
        n = random.randint(1, 4)
        chosen = random.sample(products, min(n, len(products)))

        cart = []
        for p in chosen:
            qty = random.randint(1, 3)
            cart.append({
                "product_id": p["product_id"],
                "name":       p["name"],
                "price":      p["price"],
                "quantity":   qty,
            })

        total = sum(c["price"] * c["quantity"] for c in cart)

        # ---- Payment method ----
        method = random.choice(["Cash", "Cash", "Cash", "GCash"])
        gcash_ref = None
        if method == "GCash":
            gcash_ref = f"GC{random.randint(10**9, 10**10 - 1)}"
            paid = total
        else:
            # Cash: overpay by a bit
            paid = total + random.choice([0, 5, 10, 20, 50])

        ok, result, change = create_transaction(
            user_id=user_id,
            cart=cart,
            payment_method=method,
            amount_paid=paid,
            gcash_reference=gcash_ref,
        )
        if ok:
            added += 1

    if verbose:
        print(f"[Seeder] Inserted {added} transactions.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    seed_all()