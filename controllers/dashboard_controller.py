# ─────────────────────────────────────────────
# DASHBOARD CONTROLLER
# ─────────────────────────────────────────────

from models.transaction_model import (
    get_dashboard_stats, get_profit_breakdown_today,
)
from models.product_model import get_product_counts, get_low_stock_products
from models.batch_model import count_expiring_soon, count_expired


class DashboardController:

    # ─────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────

    @staticmethod
    def get_stats():
        """Combine sales + product + batch stats into one dict."""
        stats = get_dashboard_stats()
        counts = get_product_counts()
        stats.update(counts)

        stats["expiring_soon_count"] = count_expiring_soon(days=30)
        stats["expired_count"] = count_expired()

        return stats

    # ─────────────────────────────────────────────
    # PROFIT TODAY
    # ─────────────────────────────────────────────

    @staticmethod
    def get_profit_today():
        return get_profit_breakdown_today()

    # ─────────────────────────────────────────────
    # LOW STOCK
    # ─────────────────────────────────────────────

    @staticmethod
    def low_stock_products(limit=500):
        return get_low_stock_products()[:limit]