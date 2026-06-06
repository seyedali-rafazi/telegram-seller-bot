# core/database/promo_codes.py

from .connection import get_db
from .utils import get_tehran_now_full
from .referrals import format_mb_display

PROMO_CODE_REWARD_MB = 5000
PROMO_CODE_CLAIM_MB = 5000


def make_invite_code(user_id: str) -> str:
    return f"V{str(user_id)[-8:].zfill(8)}"


async def ensure_invite_code(user_id: str) -> str:
    conn = await get_db()
    async with conn.execute(
        "SELECT invite_code FROM users WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
    if row and row[0]:
        return row[0]

    code = make_invite_code(user_id)
    for attempt in range(5):
        try:
            await conn.execute(
                "UPDATE users SET invite_code = ? WHERE user_id = ?",
                (code, user_id),
            )
            await conn.commit()
            return code
        except Exception:
            code = f"{make_invite_code(user_id)}{attempt}"
    return code


async def get_invite_code(user_id: str) -> str:
    return await ensure_invite_code(user_id)


async def resolve_invite_code(code: str) -> str | None:
    normalized = (code or "").strip().upper()
    if not normalized:
        return None
    conn = await get_db()
    async with conn.execute(
        "SELECT user_id FROM users WHERE UPPER(invite_code) = ?",
        (normalized,),
    ) as cursor:
        row = await cursor.fetchone()
    return row[0] if row else None


async def validate_promo_code_for_purchase(
    buyer_id: str, code: str
) -> tuple[bool, str, str | None]:
    normalized = (code or "").strip().upper()
    if not normalized:
        return False, "empty", None

    owner_id = await resolve_invite_code(normalized)
    if not owner_id:
        return False, "not_found", None
    if owner_id == buyer_id:
        return False, "self", None
    return True, "ok", owner_id


async def get_promo_code_stats(user_id: str) -> dict:
    conn = await get_db()
    async with conn.execute(
        """
        SELECT COALESCE(promo_code_earned_mb, 0), COALESCE(promo_code_claimed_mb, 0)
        FROM users WHERE user_id = ?
        """,
        (user_id,),
    ) as cursor:
        row = await cursor.fetchone()
    earned = row[0] if row else 0
    claimed = row[1] if row else 0

    async with conn.execute(
        """
        SELECT COUNT(*) FROM purchase_orders
        WHERE code_owner_id = ? AND promo_reward_given = 1
        """,
        (user_id,),
    ) as cursor:
        use_count = (await cursor.fetchone())[0]

    available = max(0, earned - claimed)
    return {
        "earned_mb": earned,
        "claimed_mb": claimed,
        "available_mb": available,
        "use_count": use_count,
        "invite_code": await get_invite_code(user_id),
    }


async def apply_promo_reward_for_order(order_id: int) -> dict | None:
    conn = await get_db()
    async with conn.execute(
        "SELECT * FROM purchase_orders WHERE id = ?", (order_id,)
    ) as cursor:
        order = await cursor.fetchone()
    if not order:
        return None
    if not order["code_owner_id"] or order["promo_reward_given"]:
        return None

    owner_id = order["code_owner_id"]
    buyer_id = order["user_id"]
    if owner_id == buyer_id:
        return None

    now = get_tehran_now_full()
    await conn.execute(
        """
        UPDATE users
        SET promo_code_earned_mb = COALESCE(promo_code_earned_mb, 0) + ?
        WHERE user_id = ?
        """,
        (PROMO_CODE_REWARD_MB, owner_id),
    )
    await conn.execute(
        """
        UPDATE purchase_orders
        SET promo_reward_given = 1
        WHERE id = ?
        """,
        (order_id,),
    )
    await conn.commit()

    stats = await get_promo_code_stats(owner_id)
    return {
        "owner_id": owner_id,
        "buyer_id": buyer_id,
        "reward_mb": PROMO_CODE_REWARD_MB,
        "available_display": format_mb_display(stats["available_mb"]),
        "invite_code": order["invite_code_used"] or "",
        "order_code": order["public_id"] or f"ORD-{order_id:08d}",
    }
