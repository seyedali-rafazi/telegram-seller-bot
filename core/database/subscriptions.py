# core/database/subscriptions.py

from datetime import datetime, timedelta

from .connection import get_db
from .utils import get_tehran_now_full
from .configs import assign_next_config
from .wallet import deduct_wallet
from .plans import get_plan


async def get_active_subscriptions(user_id: str):
    conn = await get_db()
    now = get_tehran_now_full()
    async with conn.execute(
        """
        SELECT s.id, p.name, s.expires_at, s.started_at
        FROM user_subscriptions s
        JOIN vpn_plans p ON p.id = s.plan_id
        WHERE s.user_id = ? AND s.is_active = 1 AND s.expires_at > ?
        ORDER BY s.expires_at DESC
        """,
        (user_id, now),
    ) as cursor:
        return await cursor.fetchall()


async def purchase_plan(user_id: str, plan_id: int) -> tuple[bool, str, dict | None]:
    plan = await get_plan(plan_id)
    if not plan or plan[5] != 1:
        return False, "plan_not_found", None

    _, name, duration_days, data_gb, price, _ = plan

    if not await deduct_wallet(user_id, price):
        return False, "insufficient_balance", {"price": price}

    config_id, config_text = await assign_next_config(user_id)
    if not config_text:
        from .wallet import adjust_wallet

        await adjust_wallet(user_id, price)
        return False, "no_config", None

    now_dt = datetime.fromisoformat(get_tehran_now_full())
    expires_dt = now_dt + timedelta(days=duration_days)
    started_at = now_dt.isoformat()
    expires_at = expires_dt.isoformat()

    conn = await get_db()
    await conn.execute(
        """
        INSERT INTO user_subscriptions
        (user_id, plan_id, config_id, started_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (user_id, plan_id, config_id, started_at, expires_at),
    )
    await conn.commit()

    return True, "ok", {
        "name": name,
        "config": config_text,
        "expires": expires_at[:10],
        "data_gb": data_gb,
        "duration_days": duration_days,
    }
