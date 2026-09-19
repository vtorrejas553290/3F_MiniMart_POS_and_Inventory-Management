# ─────────────────────────────────────────────
# REPORT CONTROLLER
# ─────────────────────────────────────────────

from models.transaction_model import (
    get_sales_today,
    get_sales_between,
    get_transactions_filtered,
    get_sales_summary,
    get_transaction_items,
    get_items_summary_for_transaction,
)
from models.activity_log_model import log_action


class ReportController:

    # ─────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────

    @staticmethod
    def today_summary():
        return get_sales_today()

    @staticmethod
    def summary(date_from=None, date_to=None):
        return get_sales_summary(date_from, date_to)

    # ─────────────────────────────────────────────
    # INDIVIDUAL TRANSACTIONS
    # ─────────────────────────────────────────────

    @staticmethod
    def list_transactions(date_from=None, date_to=None,
                          search=None, payment_method=None):
        return get_transactions_filtered(date_from, date_to,
                                         search, payment_method)

    @staticmethod
    def list_by_range(start, end):
        return get_sales_between(start, end)

    @staticmethod
    def transaction_items(transaction_id):
        return get_transaction_items(transaction_id)

    @staticmethod
    def items_summary(transaction_id):
        return get_items_summary_for_transaction(transaction_id)

    # ─────────────────────────────────────────────
    # ACCESS LOG
    # ─────────────────────────────────────────────

    @staticmethod
    def log_report_view(user, details=""):
        log_action(user["user_id"], "VIEW_REPORT", details)