# ─────────────────────────────────────────────
# TRANSACTION CONTROLLER
# ─────────────────────────────────────────────

from models.transaction_model import (
    create_transaction,
    get_transactions_filtered,
    get_transaction_items,
    get_items_summary_for_transaction,
)
from models.activity_log_model import log_action


class TransactionController:

    # ─────────────────────────────────────────────
    # WRITE
    # ─────────────────────────────────────────────

    @staticmethod
    def create(user_id, cart, payment_method, amount_paid,
               gcash_reference=None):
        """
        Create a new transaction.
        Returns (success, transaction_id_or_error, change).
        """
        return create_transaction(
            user_id=user_id,
            cart=cart,
            payment_method=payment_method,
            amount_paid=amount_paid,
            gcash_reference=gcash_reference,
        )

    # ─────────────────────────────────────────────
    # READ — LIST & DETAIL
    # ─────────────────────────────────────────────

    @staticmethod
    def list(date_from=None, date_to=None,
             search=None, payment_method=None):
        return get_transactions_filtered(date_from, date_to,
                                         search, payment_method)

    @staticmethod
    def items(transaction_id):
        return get_transaction_items(transaction_id)

    @staticmethod
    def items_summary(transaction_id):
        return get_items_summary_for_transaction(transaction_id)

    # ─────────────────────────────────────────────
    # LOG
    # ─────────────────────────────────────────────

    @staticmethod
    def log_view(user, details=""):
        log_action(user["user_id"], "VIEW_TRANSACTION", details)