# core/database/users.py

import aiosqlite  # این خط را نگه می‌داریم چون `aiosqlite.Row` نیاز به آن دارد
from .connection import get_db  # تغییر: به جای DB_NAME، از get_db استفاده می‌کنیم
from .utils import get_tehran_now_full, get_tehran_today


async def add_user(user_id, username):
    join_date = get_tehran_now_full()
    today = get_tehran_today()
    conn = await get_db()
    await conn.execute(
        """
        INSERT OR IGNORE INTO users (
            user_id, username, is_vip, join_date,
            yt_count, yt_date, music_count, music_date,
            tt_dl_count, tt_dl_date, wallet_balance, is_banned, language
        )
        VALUES (?, ?, 0, ?, 0, ?, 0, ?, 0, ?, 0, 0, 'fa')
        """,
        (user_id, username, join_date, today, today, today),
    )
    await conn.execute(
        "UPDATE users SET username = ? WHERE user_id = ?",
        (username, user_id),
    )
    await conn.commit()


async def is_user_banned(user_id: str) -> bool:
    conn = await get_db()
    async with conn.execute(
        "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return bool(row and row[0] == 1)


async def set_user_banned(user_id: str, banned: bool):
    conn = await get_db()
    await conn.execute(
        "UPDATE users SET is_banned = ? WHERE user_id = ?",
        (1 if banned else 0, user_id),
    )
    await conn.commit()


async def search_users_page(offset: int = 0, limit: int = 10):
    conn = await get_db()
    async with conn.execute(
        """
        SELECT user_id, username, wallet_balance, is_banned, join_date
        FROM users ORDER BY join_date DESC LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ) as cursor:
        return await cursor.fetchall()


async def set_vip(user_id, status: int):
    conn = await get_db()  # تغییر: استفاده از اتصال واحد
    await conn.execute(
        "UPDATE users SET is_vip = ? WHERE user_id = ?", (status, user_id)
    )
    await conn.commit()


async def get_user_info(user_id):
    conn = await get_db()  # تغییر: استفاده از اتصال واحد
    async with conn.execute(
        "SELECT username, is_vip, join_date, vip_expire_date FROM users WHERE user_id = ?",
        (user_id,),
    ) as cursor:
        return await cursor.fetchone()


async def get_full_user_info(user_id):
    """Get all user information for admin panel"""
    conn = await get_db()
    async with conn.execute(
        """SELECT user_id, username, is_vip, join_date, vip_expire_date,
                  yt_count, yt_date, music_count, music_date,
                  pinterest_count, pinterest_date, tt_dl_count, tt_dl_date,
                  gh_count, gh_date
           FROM users WHERE user_id = ?""",
        (user_id,),
    ) as cursor:
        return await cursor.fetchone()


async def get_total_users():
    conn = await get_db()  # تغییر: استفاده از اتصال واحد
    async with conn.execute("SELECT COUNT(*) FROM users") as cursor:
        return (await cursor.fetchone())[0]


async def get_all_users():
    conn = await get_db()  # تغییر: استفاده از اتصال واحد
    async with conn.execute("SELECT user_id FROM users") as cursor:
        return [row[0] for row in await cursor.fetchall()]


async def reset_user_limits(user_id):
    conn = await get_db()  # تغییر: استفاده از اتصال واحد
    await conn.execute(
        """
        UPDATE users 
        SET yt_count = 0, music_count = 0, tt_dl_count = 0
        WHERE user_id = ?
    """,
        (user_id,),
    )
    await conn.commit()


async def get_web_search_downloads(user_id):
    raise NotImplementedError("web search section removed")


async def increment_web_search_downloads(user_id):
    raise NotImplementedError("web search section removed")
