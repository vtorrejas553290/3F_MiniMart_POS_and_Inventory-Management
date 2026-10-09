# ─────────────────────────────────────────────
# SEEDER — Near-Expiry Demo Products
# ─────────────────────────────────────────────
#
# Run: python seeder_expiring.py
#
# Adds 5 products with expiration dates within the next 30 days,
# so the Dashboard "Expiring in 30 Days" panel and the "Expiring Soon"
# KPI have something to show.
#
# Requires the base seeder to have already run (needs suppliers + categories).
# If they don't exist, this script runs the base seeder first.

import random
from datetime import datetime, timedelta

from database import get_connection, now_local
from models.product_model import add_product


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _existing_product_names(conn):
    return {r["name"] for r in conn.execute("SELECT name FROM products")}


def _supplier_id(conn, name):
    row = conn.execute(
        "SELECT supplier_id FROM suppliers WHERE name = ?",
        (name,)
    ).fetchone()
    return row["supplier_id"] if row else None


def _category_id(conn, name):
    row = conn.execute(
        "SELECT category_id FROM categories WHERE name = ?",
        (name,)
    ).fetchone()
    return row["category_id"] if row else None


def _base_seed_has_run():
    conn = get_connection()
    try:
        sup = conn.execute("SELECT COUNT(*) AS c FROM suppliers").fetchone()["c"]
        cat = conn.execute("SELECT COUNT(*) AS c FROM categories").fetchone()["c"]
        return sup > 0 and cat > 0
    finally:
        conn.close()


# ─────────────────────────────────────────────
# PRODUCTS TO ADD (name, brand, size, unit, cost, price, low,
#                  supplier, category, days_from_now)
# ─────────────────────────────────────────────

NEAR_EXPIRY_PRODUCTS = [
    ("Yakult 5-Pack",              "Yakult",      "5x80ml", "pack", 45.00,  70.00, 10,
     "Coca-Cola Beverages Philippines", "Beverages",   6),
    ("Nestlé All-Purpose Cream",   "Nestlé",      "300ml",  "can",  40.00,  65.00, 10,
     "San Miguel Foods Inc.",            "Canned Goods", 9),
    ("Del Monte Pineapple Juice",  "Del Monte",   "240ml",  "can",  25.00,  40.00, 10,
     "Century Pacific Food Inc.",        "Beverages",  13),
    ("Bear Brand Sterilized",      "Bear Brand",  "300ml",  "can",  35.00,  55.00, 10,
     "Monde Nissin Corporation",         "Beverages",  23),
    ("Alaska Evaporada",           "Alaska",      "370ml",  "can",  30.00,  48.00, 10,
     "San Miguel Foods Inc.",            "Canned Goods", 27),
]


# ─────────────────────────────────────────────
# SEED
# ─────────────────────────────────────────────

def seed_near_expiry(verbose=True):
    if not _base_seed_has_run():
        if verbose:
            print("[ExpiringSeeder] Base suppliers/categories missing — "
                  "running base seeder first…")
        from seeder import seed_all
        seed_all(verbose=verbose)

    conn = get_connection()
    try:
        existing = _existing_product_names(conn)
    finally:
        conn.close()

    today = datetime.now().date()
    added = 0
    skipped = 0

    for (name, brand, size, unit, cost, price, low,
         sup_name, cat_name, days_ahead) in NEAR_EXPIRY_PRODUCTS:

        if name in existing:
            skipped += 1
            continue

        # ---- Resolve foreign keys ----
        conn = get_connection()
        try:
            sup_id = _supplier_id(conn, sup_name)
            cat_id = _category_id(conn, cat_name)
        finally:
            conn.close()

        if sup_id is None or cat_id is None:
            if verbose:
                print(f"[ExpiringSeeder] Skipped '{name}' "
                      f"(missing supplier or category)")
            continue

        # ---- Compute expiry date ----
        expiry = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

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
            if verbose:
                print(f"[ExpiringSeeder] + {name}  "
                      f"({initial_stock} units)  expires {expiry}  "
                      f"(in {days_ahead} days)")
        else:
            if verbose:
                print(f"[ExpiringSeeder] Failed: {name} — {msg}")

    if verbose:
        print(f"\n✅ Near-expiry seed complete. Added {added}, skipped {skipped}.")
        print("   Check Dashboard → 'Expiring in 30 Days' panel.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    seed_near_expiry()