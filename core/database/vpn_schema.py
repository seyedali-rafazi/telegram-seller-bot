# core/database/vpn_schema.py

from .connection import get_db
from .utils import get_tehran_now_full


async def init_vpn_tables():
    conn = await get_db()

    async with conn.execute("PRAGMA table_info(users)") as cursor:
        columns = [column[1] for column in await cursor.fetchall()]

    if "wallet_balance" not in columns:
        await conn.execute(
            "ALTER TABLE users ADD COLUMN wallet_balance INTEGER DEFAULT 0"
        )
    if "is_banned" not in columns:
        await conn.execute(
            "ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0"
        )
    if "language" not in columns:
        await conn.execute(
            "ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'fa'"
        )

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS vpn_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            data_gb INTEGER NOT NULL,
            price INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS vpn_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_text TEXT NOT NULL,
            is_assigned INTEGER DEFAULT 0,
            assigned_to TEXT,
            assigned_at TEXT,
            created_at TEXT
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS payment_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            receipt_file_id TEXT,
            status TEXT DEFAULT 'pending',
            admin_note TEXT,
            created_at TEXT,
            reviewed_at TEXT
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            plan_id INTEGER NOT NULL,
            config_id INTEGER,
            started_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (plan_id) REFERENCES vpn_plans(id),
            FOREIGN KEY (config_id) REFERENCES vpn_configs(id)
        )
    """)

    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_requests_status
        ON payment_requests(status)
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_vpn_configs_assigned
        ON vpn_configs(is_assigned)
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            plan_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            config_text TEXT,
            admin_note TEXT,
            created_at TEXT,
            reviewed_at TEXT,
            FOREIGN KEY (plan_id) REFERENCES vpn_plans(id)
        )
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_purchase_orders_status
        ON purchase_orders(status)
    """)

    async with conn.execute("PRAGMA table_info(user_subscriptions)") as cursor:
        sub_columns = [column[1] for column in await cursor.fetchall()]
    if "config_text" not in sub_columns:
        await conn.execute(
            "ALTER TABLE user_subscriptions ADD COLUMN config_text TEXT"
        )

    now = get_tehran_now_full()
    async with conn.execute("SELECT COUNT(*) FROM vpn_plans") as cursor:
        count = (await cursor.fetchone())[0]
    if count == 0:
        await conn.executemany(
            """
            INSERT INTO vpn_plans (name, duration_days, data_gb, price, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            [
                ("1 Month - 30GB", 30, 30, 150000, now),
                ("3 Months - 100GB", 90, 100, 400000, now),
            ],
        )

    await conn.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('card_number', '')"
    )
    await conn.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('card_holder', '')"
    )
    await conn.commit()
