# ─────────────────────────────────────────────
# SUPPLIER CONTROLLER
# ─────────────────────────────────────────────

from models.supplier_model import (
    get_all_suppliers, add_supplier, update_supplier,
    archive_supplier, unarchive_supplier
)
from models.supplier_category_model import (
    get_all_supplier_categories, add_supplier_category, update_supplier_category
)
from models.activity_log_model import log_action


class SupplierController:

    # ─────────────────────────────────────────────
    # SUPPLIERS
    # ─────────────────────────────────────────────

    @staticmethod
    def list_suppliers():
        return get_all_suppliers()

    @staticmethod
    def add(user, name, contact, address, supplier_category_id):
        ok, msg = add_supplier(name, contact, address, supplier_category_id)
        if ok:
            log_action(user["user_id"], "ADD_SUPPLIER", name)
        return ok, msg

    @staticmethod
    def update(user, supplier_id, name, contact, address, supplier_category_id):
        ok, msg = update_supplier(supplier_id, name, contact, address,
                                  supplier_category_id)
        if ok:
            log_action(user["user_id"], "UPDATE_SUPPLIER",
                       f"ID {supplier_id} - {name}")
        return ok, msg

    @staticmethod
    def archive(user, supplier_id, name=""):
        ok, msg = archive_supplier(supplier_id)
        if ok:
            log_action(user["user_id"], "ARCHIVE_SUPPLIER",
                       f"ID {supplier_id} - {name}")
        return ok, msg

    @staticmethod
    def unarchive(user, supplier_id, name=""):
        ok, msg = unarchive_supplier(supplier_id)
        if ok:
            log_action(user["user_id"], "UNARCHIVE_SUPPLIER",
                       f"ID {supplier_id} - {name}")
        return ok, msg

    # ─────────────────────────────────────────────
    # SUPPLIER CATEGORIES
    # ─────────────────────────────────────────────

    @staticmethod
    def list_supplier_categories():
        return get_all_supplier_categories()

    @staticmethod
    def add_supplier_category(user, name, description=""):
        ok, msg = add_supplier_category(name, description)
        if ok:
            log_action(user["user_id"], "ADD_SUPPLIER_CATEGORY", name)
        return ok, msg

    @staticmethod
    def update_supplier_category(user, scat_id, name, description=""):
        ok, msg = update_supplier_category(scat_id, name, description)
        if ok:
            log_action(user["user_id"], "UPDATE_SUPPLIER_CATEGORY",
                       f"ID {scat_id} - {name}")
        return ok, msg