# ─────────────────────────────────────────────
# INVENTORY CONTROLLER
# ─────────────────────────────────────────────

from models.product_model import (
    get_all_products, get_products_by_category,
    add_product, update_product, get_low_stock_products,
    restock_product, archive_product, unarchive_product,
    get_products_by_supplier
)
from models.category_model import (
    get_all_categories, add_category, update_category
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
    def list_by_category(category_id):
        return get_products_by_category(category_id)

    @staticmethod
    def list_by_supplier(supplier_id):
        return get_products_by_supplier(supplier_id)

    @staticmethod
    def list_low_stock():
        return get_low_stock_products()

    @staticmethod
    def add(user, name, price, stock, low, supplier_id, category_id, image_path=None):
        ok, msg = add_product(name, price, stock, low,
                              supplier_id, category_id, image_path)
        if ok:
            log_action(user["user_id"], "ADD_PRODUCT", name)
        return ok, msg

    @staticmethod
    def update(user, product_id, name, price, stock, low,
               supplier_id, category_id, image_path=None):
        ok, msg = update_product(product_id, name, price, stock, low,
                                 supplier_id, category_id, image_path)
        if ok:
            log_action(user["user_id"], "UPDATE_PRODUCT",
                       f"ID {product_id} - {name}")
        return ok, msg

    @staticmethod
    def restock(user, product_id, quantity):
        ok, msg = restock_product(product_id, quantity)
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