# core/database/referral_requests.py

from .connection import get_db
from .utils import get_tehran_now_full
from .referrals import REFERRAL_CLAIM_MB, format_mb_display


def referral_request_public_id(db_id: int) -> str:
    return f"REF-{db_id:08d}"


async def get_user_pending_referral_request(user_id: str):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, public_id, mb_amount, created_at
        FROM referral_reward_requests
        WHERE user_id = ? AND status = 'pending'
        ORDER BY id DESC LIMIT 1
        """,
        (user_id,),
    ) as cursor:
        return await cursor.fetchone()


async def create_referral_reward_request(user_id: str) -> tuple[bool, str, dict | None]:
    """
    Create admin review request and deduct ALL available referral MB from user.
    """
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id FROM referral_reward_requests
        WHERE user_id = ? AND status = 'pending' LIMIT 1
        """,
        (user_id,),
    ) as cursor:
        if await cursor.fetchone():
            return False, "pending_exists", None

    async with conn.execute(
        """
        SELECT COALESCE(referral_earned_mb, 0), COALESCE(referral_claimed_mb, 0)
        FROM users WHERE user_id = ?
        """,
        (user_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if not row:
        return False, "no_user", None

    earned, claimed = row[0], row[1]
    available = earned - claimed
    if available < REFERRAL_CLAIM_MB:
        return False, "insufficient", {"available_mb": max(0, available)}

    mb_amount = available
    now = get_tehran_now_full()
    await conn.execute(
        """
        UPDATE users
        SET referral_claimed_mb = COALESCE(referral_claimed_mb, 0) + ?
        WHERE user_id = ?
        """,
        (mb_amount, user_id),
    )
    cursor = await conn.execute(
        """
        INSERT INTO referral_reward_requests (user_id, mb_amount, status, created_at)
        VALUES (?, ?, 'pending', ?)
        """,
        (user_id, mb_amount, now),
    )
    request_id = cursor.lastrowid
    pub = referral_request_public_id(request_id)
    await conn.execute(
        "UPDATE referral_reward_requests SET public_id = ? WHERE id = ?",
        (pub, request_id),
    )
    await conn.commit()
    return True, "ok", {
        "id": request_id,
        "public_id": pub,
        "user_id": user_id,
        "mb_amount": mb_amount,
        "mb_display": format_mb_display(mb_amount),
    }


async def get_referral_request(request_id: int):
    conn = await get_db()
    async with conn.execute(
        "SELECT * FROM referral_reward_requests WHERE id = ?", (request_id,)
    ) as cursor:
        return await cursor.fetchone()


async def count_pending_referral_requests() -> int:
    conn = await get_db()
    async with conn.execute(
        "SELECT COUNT(*) FROM referral_reward_requests WHERE status = 'pending'"
    ) as cursor:
        return (await cursor.fetchone())[0]


async def get_pending_referral_requests(limit: int = 20):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, public_id, user_id, mb_amount, created_at
        FROM referral_reward_requests
        WHERE status = 'pending'
        ORDER BY id ASC LIMIT ?
        """,
        (limit,),
    ) as cursor:
        return await cursor.fetchall()


async def fulfill_referral_request(
    request_id: int, sub_url: str
) -> tuple[bool, str, dict | None]:
    req = await get_referral_request(request_id)
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
        UPDATE referral_reward_requests
        SET status = 'approved', sub_url = ?, reviewed_at = ?
        WHERE id = ?
        """,
        (sub_url, now, request_id),
    )
    await conn.commit()
    return True, "ok", {
        "user_id": req["user_id"],
        "mb_amount": req["mb_amount"],
        "mb_display": format_mb_display(req["mb_amount"]),
        "sub_url": sub_url,
        "public_id": req["public_id"] or referral_request_public_id(request_id),
        "reviewed_at": now,
    }


async def reject_referral_request(
    request_id: int,
) -> tuple[bool, str, dict | None]:
    req = await get_referral_request(request_id)
    if not req:
        return False, "not_found", None
    if req["status"] != "pending":
        return False, "already_reviewed", None

    now = get_tehran_now_full()
    conn = await get_db()
    await conn.execute(
        """
        UPDATE referral_reward_requests
        SET status = 'rejected', reviewed_at = ?
        WHERE id = ?
        """,
        (now, request_id),
    )
    await conn.execute(
        """
        UPDATE users
        SET referral_claimed_mb = MAX(0, COALESCE(referral_claimed_mb, 0) - ?)
        WHERE user_id = ?
        """,
        (req["mb_amount"], req["user_id"]),
    )
    await conn.commit()
    return True, "ok", {
        "user_id": req["user_id"],
        "mb_amount": req["mb_amount"],
        "mb_display": format_mb_display(req["mb_amount"]),
        "public_id": req["public_id"] or referral_request_public_id(request_id),
    }
