# core/database/bale_requests.py

from .connection import get_db
from .utils import get_tehran_now_full


def bale_request_public_id(db_id: int) -> str:
    return f"BALE-{db_id:08d}"


async def get_user_pending_bale_request(user_id: str):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, public_id, bale_id, created_at
        FROM bale_sub_requests
        WHERE user_id = ? AND status = 'pending'
        ORDER BY id DESC LIMIT 1
        """,
        (user_id,),
    ) as cursor:
        return await cursor.fetchone()


async def get_user_latest_approved_bale(user_id: str):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, public_id, bale_id, sub_url, reviewed_at
        FROM bale_sub_requests
        WHERE user_id = ? AND status = 'approved'
        ORDER BY id DESC LIMIT 1
        """,
        (user_id,),
    ) as cursor:
        return await cursor.fetchone()


async def get_approved_history_by_bale_id(
    bale_id: str, exclude_request_id: int | None = None, limit: int = 5
):
    conn = await get_db()
    if exclude_request_id:
        async with conn.execute(
            """
            SELECT id, public_id, user_id, sub_url, reviewed_at
            FROM bale_sub_requests
            WHERE bale_id = ? AND status = 'approved' AND id != ?
            ORDER BY id DESC LIMIT ?
            """,
            (bale_id, exclude_request_id, limit),
        ) as cursor:
            return await cursor.fetchall()
    async with conn.execute(
        """
        SELECT id, public_id, user_id, sub_url, reviewed_at
        FROM bale_sub_requests
        WHERE bale_id = ? AND status = 'approved'
        ORDER BY id DESC LIMIT ?
        """,
        (bale_id, limit),
    ) as cursor:
        return await cursor.fetchall()


async def get_approved_history_by_user_id(
    user_id: str, exclude_request_id: int | None = None, limit: int = 5
):
    conn = await get_db()
    if exclude_request_id:
        async with conn.execute(
            """
            SELECT id, public_id, bale_id, sub_url, reviewed_at
            FROM bale_sub_requests
            WHERE user_id = ? AND status = 'approved' AND id != ?
            ORDER BY id DESC LIMIT ?
            """,
            (user_id, exclude_request_id, limit),
        ) as cursor:
            return await cursor.fetchall()
    async with conn.execute(
        """
        SELECT id, public_id, bale_id, sub_url, reviewed_at
        FROM bale_sub_requests
        WHERE user_id = ? AND status = 'approved'
        ORDER BY id DESC LIMIT ?
        """,
        (user_id, limit),
    ) as cursor:
        return await cursor.fetchall()


def has_prior_bale_approval(
    bale_history: list, user_history: list, exclude_request_id: int | None = None
) -> bool:
    bale_rows = [
        r for r in bale_history if exclude_request_id is None or r[0] != exclude_request_id
    ]
    user_rows = [
        r for r in user_history if exclude_request_id is None or r[0] != exclude_request_id
    ]
    return bool(bale_rows or user_rows)


def build_bale_admin_history_text(
    bale_history: list, user_history: list, *, current_bale_id: str, current_user_id: str
) -> str:
    lines = ["📋 <b>سابقه اشتراک بله:</b>"]

    if not bale_history and not user_history:
        lines.append("✅ اولین بار — قبلاً ساب برای این درخواست ارسال نشده.")
        return "\n".join(lines)

    if bale_history:
        lines.append(f"\n🆔 شناسه بله <code>{current_bale_id}</code>:")
        for row in bale_history[:3]:
            _, pub, uid, sub_url, reviewed = row[0], row[1], row[2], row[3], row[4]
            date = (reviewed or "")[:10] or "—"
            sub_preview = (sub_url or "")[:50]
            if sub_url and len(sub_url) > 50:
                sub_preview += "…"
            lines.append(
                f"  • {pub} — کاربر <code>{uid}</code> — {date}\n"
                f"    <code>{sub_preview}</code>"
            )
    else:
        lines.append(
            f"\n✅ شناسه بله <code>{current_bale_id}</code>: قبلاً ساب ارسال نشده."
        )

    if user_history:
        lines.append(f"\n👤 کاربر تلگرام <code>{current_user_id}</code>:")
        for row in user_history[:3]:
            _, pub, bale_id, sub_url, reviewed = row[0], row[1], row[2], row[3], row[4]
            date = (reviewed or "")[:10] or "—"
            sub_preview = (sub_url or "")[:50]
            if sub_url and len(sub_url) > 50:
                sub_preview += "…"
            lines.append(
                f"  • {pub} — بله <code>{bale_id}</code> — {date}\n"
                f"    <code>{sub_preview}</code>"
            )
    else:
        lines.append(
            f"\n✅ کاربر <code>{current_user_id}</code>: قبلاً ساب بله دریافت نکرده."
        )

    if bale_history or user_history:
        lines.append("\n⚠️ <b>قبلاً ساب ارسال شده — قبل از ارسال مجدد بررسی کنید.</b>")

    return "\n".join(lines)


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
