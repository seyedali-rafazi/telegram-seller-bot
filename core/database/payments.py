# core/database/payments.py

from .connection import get_db
from .utils import get_tehran_now_full
from .wallet import adjust_wallet
from core.ids import payment_public_id


async def create_payment_request(user_id: str, amount: int, receipt_file_id: str) -> dict:
    conn = await get_db()
    now = get_tehran_now_full()
    cursor = await conn.execute(
        """
        INSERT INTO payment_requests (user_id, amount, receipt_file_id, status, created_at)
        VALUES (?, ?, ?, 'pending', ?)
        """,
        (user_id, amount, receipt_file_id, now),
    )
    payment_id = cursor.lastrowid
    pub = payment_public_id(payment_id)
    await conn.execute(
        "UPDATE payment_requests SET public_id = ? WHERE id = ?",
        (pub, payment_id),
    )
    await conn.commit()
    return {"id": payment_id, "public_id": pub}


async def get_payment(payment_id: int):
    conn = await get_db()
    async with conn.execute(
        "SELECT * FROM payment_requests WHERE id = ?", (payment_id,)
    ) as cursor:
        return await cursor.fetchone()


async def get_payment_by_public_id(public_id: str):
    conn = await get_db()
    async with conn.execute(
        "SELECT * FROM payment_requests WHERE public_id = ?", (public_id,)
    ) as cursor:
        return await cursor.fetchone()


async def get_pending_payments(limit: int = 20):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, public_id, user_id, amount, receipt_file_id, created_at
        FROM payment_requests WHERE status = 'pending'
        ORDER BY id ASC LIMIT ?
        """,
        (limit,),
    ) as cursor:
        return await cursor.fetchall()


async def count_pending_payments() -> int:
    conn = await get_db()
    async with conn.execute(
        "SELECT COUNT(*) FROM payment_requests WHERE status = 'pending'"
    ) as cursor:
        return (await cursor.fetchone())[0]


async def approve_payment(payment_id: int, admin_note: str = "") -> tuple[bool, str]:
    conn = await get_db()
    payment = await get_payment(payment_id)
    if not payment:
        return False, "not_found"
    if payment["status"] != "pending":
        return False, "already_reviewed"

    user_id = payment["user_id"]
    amount = payment["amount"]
    now = get_tehran_now_full()

    await conn.execute(
        """
        UPDATE payment_requests
        SET status = 'approved', admin_note = ?, reviewed_at = ?
        WHERE id = ?
        """,
        (admin_note, now, payment_id),
    )
    await conn.commit()
    await adjust_wallet(user_id, amount)
    return True, user_id


async def reject_payment(payment_id: int, admin_note: str = "") -> bool:
    conn = await get_db()
    payment = await get_payment(payment_id)
    if not payment or payment["status"] != "pending":
        return False
    now = get_tehran_now_full()
    await conn.execute(
        """
        UPDATE payment_requests
        SET status = 'rejected', admin_note = ?, reviewed_at = ?
        WHERE id = ?
        """,
        (admin_note, now, payment_id),
    )
    await conn.commit()
    return True
