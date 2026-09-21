# ─────────────────────────────────────────────
# REPORT CONTROLLER (aggregated analytics only)
# ─────────────────────────────────────────────

from models.transaction_model import (
    get_sales_today,
    get_sales_between,
    get_sales_summary,
    get_top_selling_products,
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
    # RANGE QUERIES
    # ─────────────────────────────────────────────

    @staticmethod
    def list_by_range(start, end):
        return get_sales_between(start, end)

    # ─────────────────────────────────────────────
    # TOP SELLING PRODUCTS
    # ─────────────────────────────────────────────

    @staticmethod
    def top_selling_products(date_from=None, date_to=None,
                             search=None, payment_method=None, limit=5):
        """
        Return the top-selling products within the given filters.

        Each row includes:
          - product_name
          - product_code
          - units_sold
          - transaction_count
          - revenue
        """
        return get_top_selling_products(
            date_from=date_from,
            date_to=date_to,
            search=search,
            payment_method=payment_method,
            limit=limit,
        )

    # ─────────────────────────────────────────────
    # ACCESS LOG
    # ─────────────────────────────────────────────

    @staticmethod
    def log_report_view(user, details=""):
        log_action(user["user_id"], "VIEW_REPORT", details)