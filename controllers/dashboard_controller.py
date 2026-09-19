# ─────────────────────────────────────────────
# DASHBOARD CONTROLLER
# ─────────────────────────────────────────────

from models.transaction_model import get_dashboard_stats, get_transactions_filtered
from models.product_model import get_product_counts, get_low_stock_products


class DashboardController:

    # ─────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────

    @staticmethod
    def get_stats():
        """Combine sales stats + product counts into one dict."""
        stats = get_dashboard_stats()
        counts = get_product_counts()
        stats.update(counts)
        return stats

    # ─────────────────────────────────────────────
    # RECENT TRANSACTIONS
    # ─────────────────────────────────────────────

    @staticmethod
    def recent_transactions(limit=5):
        """Return the latest `limit` transactions (filtered by newest first)."""
        rows = get_transactions_filtered()
        return rows[:limit]

    # ─────────────────────────────────────────────
    # LOW STOCK
    # ─────────────────────────────────────────────

    @staticmethod
    def low_stock_products(limit=5):
        """Return the products closest to running out."""
        return get_low_stock_products()[:limit]