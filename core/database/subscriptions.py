# core/database/subscriptions.py

from .connection import get_db
from .utils import get_tehran_now_full


async def get_active_subscriptions(user_id: str):
    conn = await get_db()
    now = get_tehran_now_full()
    async with conn.execute(
        """
        SELECT s.id, p.name, s.expires_at, s.started_at, s.config_text
        FROM user_subscriptions s
        JOIN vpn_plans p ON p.id = s.plan_id
        WHERE s.user_id = ? AND s.is_active = 1 AND s.expires_at > ?
        ORDER BY s.expires_at DESC
        """,
        (user_id, now),
    ) as cursor:
        return await cursor.fetchall()


async def get_user_pending_orders(user_id: str):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT o.public_id, p.name, o.amount, o.created_at
        FROM purchase_orders o
        JOIN vpn_plans p ON p.id = o.plan_id
        WHERE o.user_id = ? AND o.status = 'pending'
        ORDER BY o.id DESC
        """,
        (user_id,),
    ) as cursor:
        return await cursor.fetchall()
