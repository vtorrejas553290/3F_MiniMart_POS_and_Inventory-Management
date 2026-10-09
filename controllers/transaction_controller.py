# ─────────────────────────────────────────────
# TRANSACTION CONTROLLER
# ─────────────────────────────────────────────

from models.transaction_model import (
    create_transaction, get_transactions_filtered,
    get_transaction_items, get_sales_summary,
)


class TransactionController:

    # ─────────────────────────────────────────────
    # CREATE
    # ─────────────────────────────────────────────

    @staticmethod
    def create(user_id, cart, payment_method, amount_paid,
               gcash_reference=None):
        return create_transaction(
            user_id, cart, payment_method, amount_paid, gcash_reference
        )

    # ─────────────────────────────────────────────
    # READ
    # ─────────────────────────────────────────────

    @staticmethod
    def list(date_from=None, date_to=None, search=None,
             payment_method=None):
        rows = get_transactions_filtered(
            date_from=date_from,
            date_to=date_to,
            search=search,
            payment_method=payment_method,
        )
        # Convert sqlite3.Row → dict so callers can use .get()
        return [dict(r) for r in rows]

    @staticmethod
    def items(transaction_id):
        rows = get_transaction_items(transaction_id)
        return [dict(r) for r in rows]

    @staticmethod
    def summary(date_from=None, date_to=None):
        return get_sales_summary(date_from=date_from, date_to=date_to)

    # ─────────────────────────────────────────────
    # PROFIT
    # ─────────────────────────────────────────────

    @staticmethod
    def profit(transaction_id):
        items = get_transaction_items(transaction_id)
        profit = 0.0
        for it in items:
            cost = it["cost_price"] if "cost_price" in it.keys() else 0
            profit += (it["price"] - (cost or 0)) * it["quantity"]
        return profit