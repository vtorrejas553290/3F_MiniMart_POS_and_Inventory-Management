# ─────────────────────────────────────────────
# ACTIVITY LOG CONTROLLER
# ─────────────────────────────────────────────

from models.activity_log_model import get_logs_filtered, get_all_logs


class ActivityLogController:

    @staticmethod
    def list_all():
        return get_all_logs()

    @staticmethod
    def list_filtered(date_from=None, date_to=None, search=None):
        return get_logs_filtered(date_from, date_to, search)