# core/database/referrals.py

from .connection import get_db
from .utils import get_tehran_now_full

REFERRAL_REWARD_MB = 500
REFERRAL_CLAIM_MB = 1000


async def user_exists(user_id: str) -> bool:
    conn = await get_db()
    async with conn.execute(
        "SELECT 1 FROM users WHERE user_id = ? LIMIT 1", (user_id,)
    ) as cursor:
        return await cursor.fetchone() is not None


async def record_referral(inviter_id: str, invitee_id: str) -> bool:
    """Store pending referral for a new user. Returns True if recorded."""
    if inviter_id == invitee_id:
        return False
    if not await user_exists(inviter_id):
        return False

    conn = await get_db()
    now = get_tehran_now_full()
    try:
        await conn.execute(
            """
            INSERT INTO referrals (inviter_id, invitee_id, status, reward_mb, created_at)
            VALUES (?, ?, 'pending', ?, ?)
            """,
            (inviter_id, invitee_id, REFERRAL_REWARD_MB, now),
        )
        await conn.commit()
        return True
    except Exception:
        return False


async def qualify_referral(invitee_id: str) -> tuple[str, int] | None:
    """
    Reward inviter when invitee joins bot + channel.
    Each invitee counts once only. Returns (inviter_id, reward_mb) if rewarded.
    """
    conn = await get_db()
    async with conn.execute(
        """
        SELECT id, inviter_id, reward_mb FROM referrals
        WHERE invitee_id = ? AND status = 'pending'
        """,
        (invitee_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if not row:
        return None

    ref_id, inviter_id, reward_mb = row[0], row[1], row[2]
    if inviter_id == invitee_id or not await user_exists(inviter_id):
        await conn.execute(
            "UPDATE referrals SET status = 'invalid' WHERE id = ?", (ref_id,)
        )
        await conn.commit()
        return None

    now = get_tehran_now_full()
    await conn.execute(
        """
        UPDATE referrals
        SET status = 'rewarded', rewarded_at = ?
        WHERE id = ? AND status = 'pending'
        """,
        (now, ref_id),
    )
    await conn.execute(
        """
        UPDATE users
        SET referral_earned_mb = COALESCE(referral_earned_mb, 0) + ?
        WHERE user_id = ?
        """,
        (reward_mb, inviter_id),
    )
    await conn.commit()
    return inviter_id, reward_mb


async def get_referral_stats(user_id: str) -> dict:
    conn = await get_db()
    async with conn.execute(
        """
        SELECT COALESCE(referral_earned_mb, 0), COALESCE(referral_claimed_mb, 0)
        FROM users WHERE user_id = ?
        """,
        (user_id,),
    ) as cursor:
        row = await cursor.fetchone()
    earned = row[0] if row else 0
    claimed = row[1] if row else 0

    async with conn.execute(
        "SELECT COUNT(*) FROM referrals WHERE inviter_id = ? AND status = 'rewarded'",
        (user_id,),
    ) as cursor:
        invite_count = (await cursor.fetchone())[0]

    available = max(0, earned - claimed)
    return {
        "earned_mb": earned,
        "claimed_mb": claimed,
        "available_mb": available,
        "invite_count": invite_count,
    }


def format_mb_display(mb: int) -> str:
    if mb >= 1000 and mb % 1000 == 0:
        return f"{mb // 1000} گیگ"
    if mb >= 1000:
        gb = mb / 1000
        if gb == int(gb):
            return f"{int(gb)} گیگ"
        return f"{gb:.1f} گیگ"
    return f"{mb} مگابایت"
