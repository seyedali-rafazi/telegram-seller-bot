# core/database/orders.py

from datetime import datetime, timedelta

from .connection import get_db
from .utils import get_tehran_now_full
from .plans import get_plan
from .wallet import get_wallet_balance, deduct_wallet


async def create_purchase_order(
    user_id: str, plan_id: int
) -> tuple[bool, str, dict | None]:
    plan = await get_plan(plan_id)
    if not plan or plan[5] != 1:
        return False, "plan_not_found", None

    _, name, duration_days, data_gb, price, _ = plan
    balance = await get_wallet_balance(user_id)
    if balance < price:
        return False, "insufficient_balance", {"price": price, "balance": balance}

    now = get_tehran_now_full()
    conn = await get_db()
    cursor = await conn.execute(
        """
        INSERT INTO purchase_orders (user_id, plan_id, amount, status, created_at)
        VALUES (?, ?, ?, 'pending', ?)
        """,
        (user_id, plan_id, price, now),
    )
    await conn.commit()
    order_id = cursor.lastrowid

    return True, "pending", {
        "order_id": order_id,
        "name": name,
        "price": price,
        "duration_days": duration_days,
        "data_gb": data_gb,
    }


async def get_order(order_id: int):
    conn = await get_db()
    async with conn.execute(
        "SELECT * FROM purchase_orders WHERE id = ?", (order_id,)
    ) as cursor:
        return await cursor.fetchone()


async def get_pending_orders(limit: int = 20):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT o.id, o.user_id, o.amount, o.created_at, p.name
        FROM purchase_orders o
        JOIN vpn_plans p ON p.id = o.plan_id
        WHERE o.status = 'pending'
        ORDER BY o.id ASC LIMIT ?
        """,
        (limit,),
    ) as cursor:
        return await cursor.fetchall()


async def count_pending_orders() -> int:
    conn = await get_db()
    async with conn.execute(
        "SELECT COUNT(*) FROM purchase_orders WHERE status = 'pending'"
    ) as cursor:
        return (await cursor.fetchone())[0]


async def reject_purchase_order(order_id: int, admin_note: str = "") -> bool:
    conn = await get_db()
    order = await get_order(order_id)
    if not order or order["status"] != "pending":
        return False
    now = get_tehran_now_full()
    await conn.execute(
        """
        UPDATE purchase_orders
        SET status = 'rejected', admin_note = ?, reviewed_at = ?
        WHERE id = ?
        """,
        (admin_note, now, order_id),
    )
    await conn.commit()
    return True


async def fulfill_purchase_order(
    order_id: int, config_text: str
) -> tuple[bool, str, dict | None]:
    order = await get_order(order_id)
    if not order:
        return False, "not_found", None
    if order["status"] != "pending":
        return False, "already_reviewed", None

    config_text = config_text.strip()
    if len(config_text) < 10:
        return False, "invalid_config", None

    plan = await get_plan(order["plan_id"])
    if not plan:
        return False, "plan_not_found", None

    user_id = order["user_id"]
    _, name, duration_days, _, price, _ = plan

    if not await deduct_wallet(user_id, price):
        return False, "insufficient_balance", {"user_id": user_id, "price": price}

    now_dt = datetime.fromisoformat(get_tehran_now_full())
    expires_dt = now_dt + timedelta(days=duration_days)
    started_at = now_dt.isoformat()
    expires_at = expires_dt.isoformat()
    reviewed_at = get_tehran_now_full()

    conn = await get_db()
    sub_cursor = await conn.execute(
        """
        INSERT INTO user_subscriptions
        (user_id, plan_id, config_id, config_text, started_at, expires_at, is_active)
        VALUES (?, ?, NULL, ?, ?, ?, 1)
        """,
        (user_id, order["plan_id"], config_text, started_at, expires_at),
    )
    sub_id = sub_cursor.lastrowid
    await conn.execute(
        """
        UPDATE purchase_orders
        SET status = 'approved', config_text = ?, reviewed_at = ?
        WHERE id = ?
        """,
        (config_text, reviewed_at, order_id),
    )
    await conn.commit()

    return True, "ok", {
        "user_id": user_id,
        "name": name,
        "config": config_text,
        "expires": expires_at[:10],
        "subscription_id": sub_id,
    }
