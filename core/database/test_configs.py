# core/database/test_configs.py

from .connection import get_db
from .utils import get_tehran_now_full


async def get_user_test_config(user_id: str):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT sub_url, client_email, sub_id, created_at
        FROM test_configs WHERE user_id = ?
        """,
        (user_id,),
    ) as cursor:
        return await cursor.fetchone()


async def save_user_test_config(
    user_id: str, sub_url: str, client_email: str, sub_id: str
):
    conn = await get_db()
    now = get_tehran_now_full()
    await conn.execute(
        """
        INSERT INTO test_configs (user_id, sub_url, client_email, sub_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            sub_url = excluded.sub_url,
            client_email = excluded.client_email,
            sub_id = excluded.sub_id,
            created_at = excluded.created_at
        """,
        (user_id, sub_url, client_email, sub_id, now),
    )
    await conn.commit()
