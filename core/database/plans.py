# core/database/plans.py

from .connection import get_db
from .utils import get_tehran_now_full


async def get_active_plans():
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, name, duration_days, data_gb, price
        FROM vpn_plans WHERE is_active = 1
        ORDER BY price ASC
        """
    ) as cursor:
        return await cursor.fetchall()


async def get_all_plans():
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, name, duration_days, data_gb, price, is_active
        FROM vpn_plans ORDER BY id ASC
        """
    ) as cursor:
        return await cursor.fetchall()


async def get_plan(plan_id: int):
    conn = await get_db()
    async with conn.execute(
        "SELECT id, name, duration_days, data_gb, price, is_active FROM vpn_plans WHERE id = ?",
        (plan_id,),
    ) as cursor:
        return await cursor.fetchone()


async def create_plan(name: str, duration_days: int, data_gb: int, price: int):
    conn = await get_db()
    now = get_tehran_now_full()
    cursor = await conn.execute(
        """
        INSERT INTO vpn_plans (name, duration_days, data_gb, price, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """,
        (name, duration_days, data_gb, price, now),
    )
    await conn.commit()
    return cursor.lastrowid


async def update_plan(plan_id: int, **fields):
    allowed = {"name", "duration_days", "data_gb", "price", "is_active"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    conn = await get_db()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [plan_id]
    await conn.execute(
        f"UPDATE vpn_plans SET {set_clause} WHERE id = ?", values
    )
    await conn.commit()
    return True


async def delete_plan(plan_id: int):
    conn = await get_db()
    await conn.execute("DELETE FROM vpn_plans WHERE id = ?", (plan_id,))
    await conn.commit()
