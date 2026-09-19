# ─────────────────────────────────────────────
# RESET DATABASE (delete + recreate)
# ─────────────────────────────────────────────

import os
from config import DB_PATH
from database import initialize_database


# ─────────────────────────────────────────────
# RESET
# ─────────────────────────────────────────────

def reset():
    # ---- Delete existing DB files (main + WAL + SHM) ----
    for suffix in ["", "-wal", "-shm"]:
        path = DB_PATH + suffix
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted {path}")

    # ---- Recreate schema + default admin ----
    initialize_database()
    print("✅ Database reset.")
    print("   Default admin: admin / admin123")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    confirm = input("⚠️  This will DELETE ALL DATA. Type 'yes' to continue: ")
    if confirm.strip().lower() == "yes":
        reset()
    else:
        print("Cancelled.")