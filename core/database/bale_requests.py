# core/database/bale_requests.py

from .connection import get_db
from .utils import get_tehran_now_full


def bale_request_public_id(db_id: int) -> str:
    return f"BALE-{db_id:08d}"


async def create_bale_request(user_id: str, bale_id: str) -> dict:
    conn = await get_db()
    now = get_tehran_now_full()
    cursor = await conn.execute(
        """
        INSERT INTO bale_sub_requests (user_id, bale_id, status, created_at)
        VALUES (?, ?, 'pending', ?)
        """,
        (user_id, bale_id, now),
    )
    request_id = cursor.lastrowid
    pub = bale_request_public_id(request_id)
    await conn.execute(
        "UPDATE bale_sub_requests SET public_id = ? WHERE id = ?",
        (pub, request_id),
    )
    await conn.commit()
    return {"id": request_id, "public_id": pub, "user_id": user_id, "bale_id": bale_id}


async def get_bale_request(request_id: int):
    conn = await get_db()
    async with conn.execute(
        "SELECT * FROM bale_sub_requests WHERE id = ?", (request_id,)
    ) as cursor:
        return await cursor.fetchone()


async def count_pending_bale_requests() -> int:
    conn = await get_db()
    async with conn.execute(
        "SELECT COUNT(*) FROM bale_sub_requests WHERE status = 'pending'"
    ) as cursor:
        return (await cursor.fetchone())[0]


async def get_pending_bale_requests(limit: int = 20):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, public_id, user_id, bale_id, created_at
        FROM bale_sub_requests
        WHERE status = 'pending'
        ORDER BY id ASC LIMIT ?
        """,
        (limit,),
    ) as cursor:
        return await cursor.fetchall()


async def fulfill_bale_request(
    request_id: int, sub_url: str
) -> tuple[bool, str, dict | None]:
    req = await get_bale_request(request_id)
    if not req:
        return False, "not_found", None
    if req["status"] != "pending":
        return False, "already_reviewed", None

    sub_url = sub_url.strip()
    if len(sub_url) < 10:
        return False, "invalid_sub", None

    now = get_tehran_now_full()
    conn = await get_db()
    await conn.execute(
        """
        UPDATE bale_sub_requests
        SET status = 'approved', sub_url = ?, reviewed_at = ?
        WHERE id = ?
        """,
        (sub_url, now, request_id),
    )
    await conn.commit()
    return True, "ok", {
        "user_id": req["user_id"],
        "bale_id": req["bale_id"],
        "sub_url": sub_url,
        "public_id": req["public_id"] or bale_request_public_id(request_id),
    }
