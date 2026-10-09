# ─────────────────────────────────────────────
# INVENTORY CONTROLLER
# ─────────────────────────────────────────────

from models.product_model import (
    get_all_products, get_products_by_category,
    add_product, update_product, get_low_stock_products,
    restock_product, archive_product, unarchive_product,
    get_products_by_supplier,
)
from models.category_model import (
    get_all_categories, add_category, update_category,
)
from models.batch_model import (
    get_batches, get_expired_batches, get_expiring_soon_batches,
    discard_batch, archive_batch, update_batch as _update_batch,
)
from models.activity_log_model import log_action


class InventoryController:

    # ─────────────────────────────────────────────
    # PRODUCTS
    # ─────────────────────────────────────────────

    @staticmethod
    def list_products():
        return get_all_products()

    @staticmethod
    def list_by_category(category_id, include_archived=False):
        return get_products_by_category(category_id, include_archived)

    @staticmethod
    def list_by_supplier(supplier_id):
        return get_products_by_supplier(supplier_id)

    @staticmethod
    def list_low_stock():
        return get_low_stock_products()

    @staticmethod
    def add(user, name, price, stock, low, supplier_id, category_id,
            image_path=None, brand=None, size=None, unit="pc",
            cost_price=0.0, expiration_date=None):
        ok, msg = add_product(
            name, price, stock, low, supplier_id, category_id,
            image_path, brand, size, unit, cost_price, expiration_date,
        )
        if ok:
            log_action(user["user_id"], "ADD_PRODUCT", name)
        return ok, msg

    @staticmethod
    def update(user, product_id, name, price, low,
               supplier_id, category_id, image_path=None,
               brand=None, size=None, unit="pc", cost_price=0.0):
        ok, msg = update_product(
            product_id, name, price, low, supplier_id, category_id,
            image_path, brand, size, unit, cost_price,
        )
        if not ok:
            return ok, msg

        log_action(user["user_id"], "UPDATE_PRODUCT",
                   f"ID {product_id} - {name}")
        return True, "Product updated."

    @staticmethod
    def restock(user, product_id, quantity, cost_price=None,
                expiration_date=None):
        ok, msg = restock_product(
            product_id, quantity,
            cost_price=cost_price,
            expiration_date=expiration_date,
        )
        if ok:
            log_action(user["user_id"], "RESTOCK_PRODUCT",
                       f"ID {product_id} +{quantity}")
        return ok, msg

    @staticmethod
    def archive(user, product_id, name=""):
        ok, msg = archive_product(product_id)
        if ok:
            log_action(user["user_id"], "ARCHIVE_PRODUCT",
                       f"ID {product_id} - {name}")
        return ok, msg

    @staticmethod
    def unarchive(user, product_id, name=""):
        ok, msg = unarchive_product(product_id)
        if ok:
            log_action(user["user_id"], "UNARCHIVE_PRODUCT",
                       f"ID {product_id} - {name}")
        return ok, msg

    # ─────────────────────────────────────────────
    # BATCHES  (all return dicts, not sqlite3.Row)
    # ─────────────────────────────────────────────

    @staticmethod
    def list_batches(product_id, include_archived=False):
        rows = get_batches(product_id, include_archived)
        return [dict(r) for r in rows]

    @staticmethod
    def list_expired_batches(product_id=None):
        rows = get_expired_batches(product_id)
        return [dict(r) for r in rows]

    @staticmethod
    def list_expiring_soon(days=30, product_id=None):
        rows = get_expiring_soon_batches(days=days, product_id=product_id)
        return [dict(r) for r in rows]

    @staticmethod
    def discard_batch(user, batch_id, quantity=None):
        ok, msg = discard_batch(batch_id, quantity)
        if ok:
            log_action(user["user_id"], "DISCARD_BATCH",
                       f"batch_id={batch_id} qty={quantity or 'all'}")
        return ok, msg

    @staticmethod
    def update_batch(user, batch_id, quantity=None, cost_price=None,
                     expiration_date="__KEEP__"):
        ok, msg = _update_batch(batch_id, quantity, cost_price, expiration_date)
        if ok:
            log_action(user["user_id"], "UPDATE_BATCH",
                       f"batch_id={batch_id}")
        return ok, msg

    @staticmethod
    def archive_batch(user, batch_id):
        ok, msg = archive_batch(batch_id)
        if ok:
            log_action(user["user_id"], "ARCHIVE_BATCH",
                       f"batch_id={batch_id}")
        return ok, msg

    # ─────────────────────────────────────────────
    # CATEGORIES
    # ─────────────────────────────────────────────

    @staticmethod
    def list_categories():
        return get_all_categories()

    @staticmethod
    def add_category(user, name, description=""):
        ok, msg = add_category(name, description)
        if ok:
            log_action(user["user_id"], "ADD_CATEGORY", name)
        return ok, msg

    @staticmethod
    def update_category(user, category_id, name, description=""):
        ok, msg = update_category(category_id, name, description)
        if ok:
            log_action(user["user_id"], "UPDATE_CATEGORY",
                       f"ID {category_id} - {name}")
        return ok, msg