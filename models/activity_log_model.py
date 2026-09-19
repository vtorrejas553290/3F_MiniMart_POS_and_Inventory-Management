# ─────────────────────────────────────────────
# ACTIVITY LOG MODEL
# ─────────────────────────────────────────────

import time
from database import get_connection, now_local


# ─────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────

def log_action(user_id, action, details="", retries=3):
    for attempt in range(retries):
        conn = get_connection()
        try:
            conn.execute("""
                INSERT INTO activity_logs (user_id, action, details, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, action, details, now_local()))
            conn.commit()
            conn.close()
            return
        except Exception as e:
            conn.close()
            if attempt < retries - 1:
                time.sleep(0.2)
            else:
                print(f"[LOG] Failed to log action: {e}")


# ─────────────────────────────────────────────
# READ — ALL (existing)
# ─────────────────────────────────────────────

def get_all_logs(limit=500):
    conn = get_connection()
    rows = conn.execute("""
        SELECT l.*, u.username, u.full_name
        FROM activity_logs l
        JOIN users u ON l.user_id = u.user_id
        ORDER BY l.created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


# ─────────────────────────────────────────────
# READ — FILTERED (date range + search)
# ─────────────────────────────────────────────

def get_logs_filtered(date_from=None, date_to=None, search=None, limit=1000):
    """
    Return activity logs filtered by:
      - date range (YYYY-MM-DD) on created_at
      - search term (username, full_name, action, details)
    """
    conn = get_connection()
    sql = """
        SELECT l.*, u.username, u.full_name
        FROM activity_logs l
        JOIN users u ON l.user_id = u.user_id
        WHERE 1=1
    """
    params = []

    if date_from:
        sql += " AND DATE(l.created_at) >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND DATE(l.created_at) <= ?"
        params.append(date_to)
    if search:
        q = f"%{search.lower()}%"
        sql += """ AND (
            LOWER(u.username)  LIKE ?
            OR LOWER(u.full_name) LIKE ?
            OR LOWER(l.action)    LIKE ?
            OR LOWER(l.details)   LIKE ?
        )"""
        params.extend([q, q, q, q])

    sql += " ORDER BY l.created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows