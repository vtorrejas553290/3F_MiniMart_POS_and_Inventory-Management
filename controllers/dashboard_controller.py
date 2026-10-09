# ─────────────────────────────────────────────
# DASHBOARD CONTROLLER
# ─────────────────────────────────────────────

from models.transaction_model import get_dashboard_stats
from models.product_model import get_all_products
from models.batch_model import (
    count_expiring_soon, count_expired,
    get_expiring_soon_batches, get_expired_batches,
)


class DashboardController:

    @staticmethod
    def get_stats():
        """
        Compute dashboard stats with ONE product fetch shared across
        all product-derived numbers.
        """
        stats = get_dashboard_stats()

        # ---- Fetch products ONCE ----
        products = get_all_products(include_archived=False)

        total_products = len(products)
        low_count = sum(
            1 for p in products
            if 0 < p["stock_qty"] <= (p["low_stock_level"] or 0)
        )
        out_count = sum(1 for p in products if p["stock_qty"] <= 0)

        stats["total_products"]     = total_products
        stats["low_stock_count"]    = low_count
        stats["out_of_stock_count"] = out_count

        # ---- Batch aggregates ----
        stats["expiring_soon_count"] = count_expiring_soon(days=30)
        stats["expired_count"]       = count_expired()

        return stats

    @staticmethod
    def low_stock_products(limit=500):
        products = get_all_products(include_archived=False)
        rows = [
            p for p in products
            if p["stock_qty"] <= (p["low_stock_level"] or 0)
        ]
        return rows[:limit]