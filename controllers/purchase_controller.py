# ─────────────────────────────────────────────
# PURCHASE CONTROLLER
# ─────────────────────────────────────────────

from models.purchase_model import (
    create_purchase, receive_purchase, cancel_purchase,
    get_all_purchases, get_purchase, get_purchase_items,
    get_purchases_by_supplier,
)
from models.activity_log_model import log_action


class PurchaseController:

    @staticmethod
    def list_all():
        return get_all_purchases()

    @staticmethod
    def list_by_status(status):
        return get_all_purchases(status=status)

    @staticmethod
    def list_by_supplier(supplier_id):
        return get_purchases_by_supplier(supplier_id)

    @staticmethod
    def get(purchase_id):
        return get_purchase(purchase_id)

    @staticmethod
    def get_items(purchase_id):
        return get_purchase_items(purchase_id)

    @staticmethod
    def create(user, supplier_id, items, notes=""):
        """
        items = list of dicts:
            {product_id, quantity, cost, expiration_date?}
        """
        if not items:
            return False, "No items in the purchase order."
        ok, result = create_purchase(supplier_id, user["user_id"], items, notes)
        if ok:
            log_action(user["user_id"], "CREATE_PURCHASE",
                       f"PO #{result} | Supplier ID {supplier_id}")
        return ok, result

    @staticmethod
    def receive(user, purchase_id, product_ids=None):
        """
        Mark a purchase order as Received and add its items to inventory.

        Parameters
        ----------
        user : dict
        purchase_id : int
        product_ids : list[int] | None
            If provided, only these product_ids will be received.
            If None, all items on the PO will be received (original behavior).
        """
        ok, msg = receive_purchase(
            purchase_id,
            user["user_id"],
            product_ids=product_ids,
        )
        if ok:
            if product_ids:
                log_action(
                    user["user_id"],
                    "RECEIVE_PURCHASE",
                    f"PO #{purchase_id} | Received {len(product_ids)} item(s)",
                )
            else:
                log_action(user["user_id"], "RECEIVE_PURCHASE",
                           f"PO #{purchase_id}")
        return ok, msg

    @staticmethod
    def cancel(user, purchase_id):
        ok, msg = cancel_purchase(purchase_id)
        if ok:
            log_action(user["user_id"], "CANCEL_PURCHASE", f"PO #{purchase_id}")
        return ok, msg