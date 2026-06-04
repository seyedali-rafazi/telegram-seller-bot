# core/database/user_orders.py

from .connection import get_db
from .utils import get_tehran_now_full


async def get_user_pending_orders_detailed(user_id: str):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT o.id, o.public_id, p.name, o.amount, o.created_at
        FROM purchase_orders o
        JOIN vpn_plans p ON p.id = o.plan_id
        WHERE o.user_id = ? AND o.status = 'pending'
        ORDER BY o.id ASC
        """,
        (user_id,),
    ) as cursor:
        return await cursor.fetchall()


async def get_user_orders_history(user_id: str, status: str | None = None, limit: int = 30):
    conn = await get_db()
    if status:
        async with conn.execute(
            """
            SELECT o.id, o.public_id, o.status, p.name, o.amount, o.created_at,
                   o.config_text, o.reviewed_at
            FROM purchase_orders o
            JOIN vpn_plans p ON p.id = o.plan_id
            WHERE o.user_id = ? AND o.status = ?
            ORDER BY o.id DESC LIMIT ?
            """,
            (user_id, status, limit),
        ) as cursor:
            return await cursor.fetchall()
    async with conn.execute(
        """
        SELECT o.id, o.public_id, o.status, p.name, o.amount, o.created_at,
               o.config_text, o.reviewed_at
        FROM purchase_orders o
        JOIN vpn_plans p ON p.id = o.plan_id
        WHERE o.user_id = ?
        ORDER BY o.id DESC LIMIT ?
        """,
        (user_id, limit),
    ) as cursor:
        return await cursor.fetchall()


async def count_user_orders_by_status(user_id: str) -> dict:
    conn = await get_db()
    counts = {"pending": 0, "approved": 0, "rejected": 0}
    async with conn.execute(
        """
        SELECT status, COUNT(*) FROM purchase_orders
        WHERE user_id = ? GROUP BY status
        """,
        (user_id,),
    ) as cursor:
        for status, cnt in await cursor.fetchall():
            if status in counts:
                counts[status] = cnt
    return counts


async def get_user_subscriptions_all(user_id: str, limit: int = 30):
    conn = await get_db()
    now = get_tehran_now_full()
    async with conn.execute(
        """
        SELECT s.id, s.public_id, p.name, s.expires_at, s.started_at, s.config_text,
               CASE WHEN s.is_active = 1 AND s.expires_at > ? THEN 1 ELSE 0 END AS is_live
        FROM user_subscriptions s
        JOIN vpn_plans p ON p.id = s.plan_id
        WHERE s.user_id = ?
        ORDER BY s.id DESC LIMIT ?
        """,
        (now, user_id, limit),
    ) as cursor:
        return await cursor.fetchall()


async def get_subscription_by_id(sub_id: int):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT s.*, p.name AS plan_name
        FROM user_subscriptions s
        JOIN vpn_plans p ON p.id = s.plan_id
        WHERE s.id = ?
        """,
        (sub_id,),
    ) as cursor:
        return await cursor.fetchone()
