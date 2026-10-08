# ─────────────────────────────────────────────
# POS CONTROLLER (cart + checkout)
# ─────────────────────────────────────────────

from models.transaction_model import create_transaction
from models.activity_log_model import log_action


# ─────────────────────────────────────────────
# sqlite3.Row-safe getter
# ─────────────────────────────────────────────

def _row_get(row, key, default=None):
    """Read a key from a sqlite3.Row or dict without raising."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return default


class POSController:

    # ─────────────────────────────────────────────
    # CART STATE
    # ─────────────────────────────────────────────

    def __init__(self):
        self.cart = []

    # ─────────────────────────────────────────────
    # ADD / REMOVE
    # ─────────────────────────────────────────────

    def add_to_cart(self, product, qty=1):
        """
        Add a product to the cart with the given quantity.
        If the product is already in the cart, increment its quantity.

        Returns:
            True  → added/incremented successfully
        """
        for item in self.cart:
            if item["product_id"] == product["product_id"]:
                item["quantity"] += qty
                return True

        self.cart.append({
            "product_id": product["product_id"],
            "name":       product["name"],
            "brand":      _row_get(product, "brand"),
            "size":       _row_get(product, "size"),
            "unit":       _row_get(product, "unit"),
            "price":      product["price"],
            "quantity":   qty,
        })
        return True

    def remove_from_cart(self, product_id):
        self.cart = [i for i in self.cart if i["product_id"] != product_id]

    # ─────────────────────────────────────────────
    # QUANTITY ADJUSTMENT
    # ─────────────────────────────────────────────

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

    def increase_quantity(self, product_id, max_qty=None):
        """
        Increase the quantity of a cart item by 1, clamped to max_qty.
        Returns the new quantity (or current if not found / at max).
        """
        for item in self.cart:
            if item["product_id"] == product_id:
                if max_qty is not None and item["quantity"] >= max_qty:
                    return item["quantity"]
                item["quantity"] += 1
                return item["quantity"]
        return 0

    def set_quantity(self, product_id, qty, max_qty=None):
        """
        Set the quantity for a cart item.
        - qty <= 0        → remove item
        - max_qty given   → clamp to max_qty
        Returns the resulting quantity (0 if removed).
        """
        if qty <= 0:
            self.remove_from_cart(product_id)
            return 0

        if max_qty is not None and qty > max_qty:
            qty = max_qty

        for item in self.cart:
            if item["product_id"] == product_id:
                item["quantity"] = qty
                return qty

        return 0

    def get_quantity(self, product_id):
        """Return the quantity of a product currently in the cart (0 if absent)."""
        for item in self.cart:
            if item["product_id"] == product_id:
                return item["quantity"]
        return 0

    # ─────────────────────────────────────────────
    # MISC
    # ─────────────────────────────────────────────

    def clear_cart(self):
        self.cart = []

    def get_total(self):
        return sum(i["price"] * i["quantity"] for i in self.cart)

    # ─────────────────────────────────────────────
    # CHECKOUT
    # ─────────────────────────────────────────────

    def checkout(self, user, payment_method, amount_paid,
                 gcash_reference=None):
        if not self.cart:
            return False, "Cart is empty.", 0

        ok, result, change = create_transaction(
            user["user_id"], self.cart, payment_method, amount_paid,
            gcash_reference
        )
        if ok:
            ref_str = f" | Ref: {gcash_reference}" if gcash_reference else ""
            log_action(
                user["user_id"],
                "SALE",
                f"Txn #{result} | Total: {self.get_total():.2f} | {payment_method}{ref_str}"
            )
            self.clear_cart()
        return ok, result, change