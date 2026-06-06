# core/database/referral_configs.py

from .connection import get_db
from .utils import get_tehran_now_full
from .referrals import REFERRAL_CLAIM_MB


async def get_user_referral_config(user_id: str):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT sub_url, created_at FROM referral_configs
        WHERE user_id = ? ORDER BY id DESC LIMIT 1
        """,
        (user_id,),
    ) as cursor:
        return await cursor.fetchone()


async def claim_referral_internet(user_id: str) -> tuple[bool, str, str | None]:
    """
    Spend REFERRAL_CLAIM_MB from user's referral balance and assign a sub URL.
    Returns (ok, reason, sub_url).
    """
    conn = await get_db()
    async with conn.execute(
        """
        SELECT COALESCE(referral_earned_mb, 0), COALESCE(referral_claimed_mb, 0)
        FROM users WHERE user_id = ?
        """,
        (user_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if not row:
        return False, "no_user", None

    earned, claimed = row[0], row[1]
    available = earned - claimed
    if available < REFERRAL_CLAIM_MB:
        return False, "insufficient", None

    async with conn.execute(
        """
        SELECT id, sub_url FROM referral_config_pool
        WHERE is_assigned = 0 ORDER BY id ASC LIMIT 1
        """
    ) as cursor:
        pool_row = await cursor.fetchone()
    if not pool_row:
        return False, "empty_pool", None

    pool_id, sub_url = pool_row[0], pool_row[1]
    now = get_tehran_now_full()

    await conn.execute(
        """
        UPDATE referral_config_pool
        SET is_assigned = 1, assigned_to = ?, assigned_at = ?
        WHERE id = ? AND is_assigned = 0
        """,
        (user_id, now, pool_id),
    )
    await conn.execute(
        """
        UPDATE users
        SET referral_claimed_mb = COALESCE(referral_claimed_mb, 0) + ?
        WHERE user_id = ?
        """,
        (REFERRAL_CLAIM_MB, user_id),
    )
    await conn.execute(
        """
        INSERT INTO referral_configs (user_id, sub_url, mb_spent, pool_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, sub_url, REFERRAL_CLAIM_MB, pool_id, now),
    )
    await conn.commit()
    return True, "ok", sub_url


async def add_referral_configs_bulk(lines: list[str]) -> int:
    conn = await get_db()
    now = get_tehran_now_full()
    added = 0
    for line in lines:
        text = line.strip()
        if not text or len(text) < 10:
            continue
        await conn.execute(
            """
            INSERT INTO referral_config_pool (sub_url, is_assigned, created_at)
            VALUES (?, 0, ?)
            """,
            (text, now),
        )
        added += 1
    await conn.commit()
    return added


async def count_available_referral_configs() -> int:
    conn = await get_db()
    async with conn.execute(
        "SELECT COUNT(*) FROM referral_config_pool WHERE is_assigned = 0"
    ) as cursor:
        return (await cursor.fetchone())[0]


async def count_total_referral_configs() -> int:
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) FROM referral_config_pool") as cursor:
        return (await cursor.fetchone())[0]


async def list_referral_config_pool(limit: int = 25):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, sub_url, is_assigned, assigned_to, created_at
        FROM referral_config_pool
        ORDER BY id DESC LIMIT ?
        """,
        (limit,),
    ) as cursor:
        return await cursor.fetchall()


async def delete_referral_pool_item(pool_id: int) -> tuple[bool, str]:
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, is_assigned, assigned_to
        FROM referral_config_pool WHERE id = ?
        """,
        (pool_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if not row:
        return False, "not_found"

    if row["is_assigned"] and row["assigned_to"]:
        await conn.execute(
            "DELETE FROM referral_configs WHERE user_id = ? AND pool_id = ?",
            (row["assigned_to"], pool_id),
        )
    await conn.execute("DELETE FROM referral_config_pool WHERE id = ?", (pool_id,))
    await conn.commit()
    return True, "ok"
