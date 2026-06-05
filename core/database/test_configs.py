# core/database/test_configs.py

from .connection import get_db
from .utils import get_tehran_now_full


async def get_user_test_config(user_id: str):
    conn = await get_db()
    async with conn.execute(
        "SELECT sub_url FROM test_configs WHERE user_id = ?",
        (user_id,),
    ) as cursor:
        return await cursor.fetchone()


async def assign_test_config_to_user(user_id: str) -> str | None:
    """Return sub_url for user. Reuses existing assignment or takes next free pool item."""
    existing = await get_user_test_config(user_id)
    if existing:
        return existing[0]

    conn = await get_db()
    now = get_tehran_now_full()
    async with conn.execute(
        """
        SELECT id, sub_url FROM test_config_pool
        WHERE is_assigned = 0 ORDER BY id ASC LIMIT 1
        """
    ) as cursor:
        row = await cursor.fetchone()
    if not row:
        return None

    pool_id, sub_url = row[0], row[1]
    await conn.execute(
        """
        UPDATE test_config_pool
        SET is_assigned = 1, assigned_to = ?, assigned_at = ?
        WHERE id = ? AND is_assigned = 0
        """,
        (user_id, now, pool_id),
    )
    await conn.execute(
        """
        INSERT INTO test_configs (user_id, sub_url, pool_id, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, sub_url, pool_id, now),
    )
    await conn.commit()
    return sub_url


async def add_test_configs_bulk(lines: list[str]) -> int:
    conn = await get_db()
    now = get_tehran_now_full()
    added = 0
    for line in lines:
        text = line.strip()
        if not text or len(text) < 10:
            continue
        await conn.execute(
            """
            INSERT INTO test_config_pool (sub_url, is_assigned, created_at)
            VALUES (?, 0, ?)
            """,
            (text, now),
        )
        added += 1
    await conn.commit()
    return added


async def count_available_test_configs() -> int:
    conn = await get_db()
    async with conn.execute(
        "SELECT COUNT(*) FROM test_config_pool WHERE is_assigned = 0"
    ) as cursor:
        return (await cursor.fetchone())[0]


async def count_total_test_configs() -> int:
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) FROM test_config_pool") as cursor:
        return (await cursor.fetchone())[0]


async def list_test_config_pool(limit: int = 25):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, sub_url, is_assigned, assigned_to, created_at
        FROM test_config_pool
        ORDER BY id DESC LIMIT ?
        """,
        (limit,),
    ) as cursor:
        return await cursor.fetchall()


async def delete_test_pool_item(pool_id: int) -> tuple[bool, str]:
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, is_assigned, assigned_to
        FROM test_config_pool WHERE id = ?
        """,
        (pool_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if not row:
        return False, "not_found"

    if row["is_assigned"] and row["assigned_to"]:
        await conn.execute(
            "DELETE FROM test_configs WHERE user_id = ?",
            (row["assigned_to"],),
        )
    await conn.execute("DELETE FROM test_config_pool WHERE id = ?", (pool_id,))
    await conn.commit()
    return True, "ok"
