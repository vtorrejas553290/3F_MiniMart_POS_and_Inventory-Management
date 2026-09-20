# ─────────────────────────────────────────────
# POS CONTROLLER (cart + checkout)
# ─────────────────────────────────────────────

from models.transaction_model import create_transaction
from models.activity_log_model import log_action


class POSController:

    # ─────────────────────────────────────────────
    # CART STATE
    # ─────────────────────────────────────────────

    def __init__(self):
        self.cart = []

    def add_to_cart(self, product, qty=1):
        for item in self.cart:
            if item["product_id"] == product["product_id"]:
                item["quantity"] += qty
                return
        self.cart.append({
            "product_id": product["product_id"],
            "name":       product["name"],
            "price":      product["price"],
            "quantity":   qty,
        })

    def remove_from_cart(self, product_id):
        self.cart = [i for i in self.cart if i["product_id"] != product_id]

    # ---- NEW: decrease quantity by 1 ----
    def decrease_quantity(self, product_id):
        """
        Decrease the quantity of a cart item by 1.
        If quantity reaches 0, remove the item entirely.
        Returns the new quantity (0 if removed).
        """
        for item in self.cart:
            if item["product_id"] == product_id:
                item["quantity"] -= 1
                if item["quantity"] <= 0:
                    self.remove_from_cart(product_id)
                    return 0
                return item["quantity"]
        return 0

    def clear_cart(self):
        self.cart = []

    def get_total(self):
        return sum(i["price"] * i["quantity"] for i in self.cart)

    # ─────────────────────────────────────────────
    # CHECKOUT
    # ─────────────────────────────────────────────

    def checkout(self, user, payment_method, amount_paid):
        if not self.cart:
            return False, "Cart is empty.", 0

        ok, result, change = create_transaction(
            user["user_id"], self.cart, payment_method, amount_paid
        )
        if ok:
            log_action(
                user["user_id"],
                "SALE",
                f"Txn #{result} | Total: {self.get_total():.2f} | {payment_method}"
            )
            self.clear_cart()
        return ok, result, change