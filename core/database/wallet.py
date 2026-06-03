# core/database/wallet.py

from .connection import get_db


async def get_wallet_balance(user_id: str) -> int:
    conn = await get_db()
    async with conn.execute(
        "SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else 0


async def adjust_wallet(user_id: str, delta: int) -> int:
    conn = await get_db()
    await conn.execute(
        "UPDATE users SET wallet_balance = COALESCE(wallet_balance, 0) + ? WHERE user_id = ?",
        (delta, user_id),
    )
    await conn.commit()
    return await get_wallet_balance(user_id)


async def set_wallet_balance(user_id: str, amount: int) -> int:
    conn = await get_db()
    await conn.execute(
        "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
        (max(0, amount), user_id),
    )
    await conn.commit()
    return await get_wallet_balance(user_id)


async def deduct_wallet(user_id: str, amount: int) -> bool:
    balance = await get_wallet_balance(user_id)
    if balance < amount:
        return False
    await adjust_wallet(user_id, -amount)
    return True
