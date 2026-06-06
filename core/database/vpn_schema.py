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
    if "referral_earned_mb" not in columns:
        await conn.execute(
            "ALTER TABLE users ADD COLUMN referral_earned_mb INTEGER DEFAULT 0"
        )
    if "referral_claimed_mb" not in columns:
        await conn.execute(
            "ALTER TABLE users ADD COLUMN referral_claimed_mb INTEGER DEFAULT 0"
        )
    if "invite_code" not in columns:
        await conn.execute("ALTER TABLE users ADD COLUMN invite_code TEXT")
    if "promo_code_earned_mb" not in columns:
        await conn.execute(
            "ALTER TABLE users ADD COLUMN promo_code_earned_mb INTEGER DEFAULT 0"
        )
    if "promo_code_claimed_mb" not in columns:
        await conn.execute(
            "ALTER TABLE users ADD COLUMN promo_code_claimed_mb INTEGER DEFAULT 0"
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

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS test_configs (
            user_id TEXT PRIMARY KEY,
            sub_url TEXT NOT NULL,
            pool_id INTEGER,
            created_at TEXT
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS test_config_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_url TEXT NOT NULL,
            is_assigned INTEGER DEFAULT 0,
            assigned_to TEXT,
            assigned_at TEXT,
            created_at TEXT
        )
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_test_config_pool_assigned
        ON test_config_pool(is_assigned)
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS bale_sub_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            public_id TEXT,
            user_id TEXT NOT NULL,
            bale_id TEXT NOT NULL,
            sub_url TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            reviewed_at TEXT
        )
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_bale_sub_requests_status
        ON bale_sub_requests(status)
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_bale_sub_requests_user_status
        ON bale_sub_requests(user_id, status)
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_bale_sub_requests_bale_status
        ON bale_sub_requests(bale_id, status)
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter_id TEXT NOT NULL,
            invitee_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'pending',
            reward_mb INTEGER NOT NULL DEFAULT 500,
            created_at TEXT NOT NULL,
            rewarded_at TEXT
        )
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_referrals_inviter
        ON referrals(inviter_id)
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_referrals_invitee_status
        ON referrals(invitee_id, status)
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS referral_reward_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            public_id TEXT,
            user_id TEXT NOT NULL,
            mb_amount INTEGER NOT NULL,
            source TEXT DEFAULT 'link',
            sub_url TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            reviewed_at TEXT
        )
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_referral_reward_requests_status
        ON referral_reward_requests(status)
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_referral_reward_requests_user_status
        ON referral_reward_requests(user_id, status)
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS referral_config_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_url TEXT NOT NULL,
            is_assigned INTEGER DEFAULT 0,
            assigned_to TEXT,
            assigned_at TEXT,
            created_at TEXT
        )
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_referral_config_pool_assigned
        ON referral_config_pool(is_assigned)
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS referral_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            sub_url TEXT NOT NULL,
            mb_spent INTEGER NOT NULL,
            pool_id INTEGER,
            created_at TEXT NOT NULL
        )
    """)

    async with conn.execute("PRAGMA table_info(test_configs)") as cursor:
        test_cols = [column[1] for column in await cursor.fetchall()]
    if test_cols and "pool_id" not in test_cols:
        await conn.execute("ALTER TABLE test_configs ADD COLUMN pool_id INTEGER")

    async with conn.execute("PRAGMA table_info(user_subscriptions)") as cursor:
        sub_columns = [column[1] for column in await cursor.fetchall()]
    if "config_text" not in sub_columns:
        await conn.execute(
            "ALTER TABLE user_subscriptions ADD COLUMN config_text TEXT"
        )

    async with conn.execute("PRAGMA table_info(purchase_orders)") as cursor:
        order_cols = [column[1] for column in await cursor.fetchall()]
    if order_cols and "invite_code_used" not in order_cols:
        await conn.execute(
            "ALTER TABLE purchase_orders ADD COLUMN invite_code_used TEXT"
        )
    if order_cols and "code_owner_id" not in order_cols:
        await conn.execute(
            "ALTER TABLE purchase_orders ADD COLUMN code_owner_id TEXT"
        )
    if order_cols and "promo_reward_given" not in order_cols:
        await conn.execute(
            "ALTER TABLE purchase_orders ADD COLUMN promo_reward_given INTEGER DEFAULT 0"
        )
    if order_cols and "receipt_file_id" not in order_cols:
        await conn.execute(
            "ALTER TABLE purchase_orders ADD COLUMN receipt_file_id TEXT"
        )

    async with conn.execute("PRAGMA table_info(referral_reward_requests)") as cursor:
        ref_req_cols = [column[1] for column in await cursor.fetchall()]
    if ref_req_cols and "source" not in ref_req_cols:
        await conn.execute(
            "ALTER TABLE referral_reward_requests ADD COLUMN source TEXT DEFAULT 'link'"
        )

    await conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_invite_code "
        "ON users(invite_code) WHERE invite_code IS NOT NULL"
    )

    from .promo_codes import make_invite_code

    async with conn.execute(
        "SELECT user_id FROM users WHERE invite_code IS NULL OR invite_code = ''"
    ) as cursor:
        for (uid,) in await cursor.fetchall():
            code = make_invite_code(uid)
            await conn.execute(
                "UPDATE users SET invite_code = ? WHERE user_id = ?",
                (code, uid),
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

    from core.ids import payment_public_id, order_public_id, subscription_public_id
    from .referral_requests import referral_request_public_id

    async def _add_public_id(table: str, maker):
        async with conn.execute(f"PRAGMA table_info({table})") as cursor:
            cols = [c[1] for c in await cursor.fetchall()]
        if "public_id" not in cols:
            await conn.execute(f"ALTER TABLE {table} ADD COLUMN public_id TEXT")
        async with conn.execute(
            f"SELECT id FROM {table} WHERE public_id IS NULL OR public_id = ''"
        ) as cursor:
            for (row_id,) in await cursor.fetchall():
                await conn.execute(
                    f"UPDATE {table} SET public_id = ? WHERE id = ?",
                    (maker(row_id), row_id),
                )
        await conn.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_public_id "
            f"ON {table}(public_id)"
        )

    await _add_public_id("payment_requests", payment_public_id)
    await _add_public_id("purchase_orders", order_public_id)
    await _add_public_id("user_subscriptions", subscription_public_id)
    await _add_public_id("referral_reward_requests", referral_request_public_id)

    await conn.commit()
