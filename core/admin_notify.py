# core/admin_notify.py

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.config import get_admin_ids

logger = logging.getLogger(__name__)


async def notify_admins(
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    photo_file_id: str | None = None,
    caption: str | None = None,
    parse_mode: str | None = None,
) -> int:
    """ارسال پیام به همه ادمین‌ها. تعداد موفق را برمی‌گرداند."""
    admin_ids = get_admin_ids()
    if not admin_ids:
        logger.error(
            "ADMIN_ID در .env تنظیم نشده — ادمین اطلاع نمی‌گیرد. "
            "شناسه خود را با /myid بگیرید و در .env بگذارید."
        )
        return 0

    sent = 0
    for admin_id in admin_ids:
        try:
            if photo_file_id:
                await context.bot.send_photo(
                    chat_id=int(admin_id),
                    photo=photo_file_id,
                    caption=caption or text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )
            else:
                await context.bot.send_message(
                    chat_id=int(admin_id),
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )
            sent += 1
        except Exception:
            logger.exception("Failed to notify admin %s", admin_id)
    return sent
