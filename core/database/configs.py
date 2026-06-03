# core/database/configs.py

from .connection import get_db
from .utils import get_tehran_now_full


async def add_configs_bulk(lines: list[str]) -> int:
    conn = await get_db()
    now = get_tehran_now_full()
    added = 0
    for line in lines:
        text = line.strip()
        if not text or len(text) < 10:
            continue
        await conn.execute(
            """
            INSERT INTO vpn_configs (config_text, is_assigned, created_at)
            VALUES (?, 0, ?)
            """,
            (text, now),
        )
        added += 1
    await conn.commit()
    return added


async def assign_next_config(user_id: str):
    conn = await get_db()
    now = get_tehran_now_full()
    async with conn.execute(
        """
        SELECT id, config_text FROM vpn_configs
        WHERE is_assigned = 0 ORDER BY id ASC LIMIT 1
        """
    ) as cursor:
        row = await cursor.fetchone()
    if not row:
        return None, None

    config_id, config_text = row[0], row[1]
    await conn.execute(
        """
        UPDATE vpn_configs
        SET is_assigned = 1, assigned_to = ?, assigned_at = ?
        WHERE id = ?
        """,
        (user_id, now, config_id),
    )
    await conn.commit()
    return config_id, config_text


async def count_available_configs() -> int:
    conn = await get_db()
    async with conn.execute(
        "SELECT COUNT(*) FROM vpn_configs WHERE is_assigned = 0"
    ) as cursor:
        return (await cursor.fetchone())[0]


async def count_total_configs() -> int:
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) FROM vpn_configs") as cursor:
        return (await cursor.fetchone())[0]
