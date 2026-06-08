# main.py

import logging
import os

from dotenv import load_dotenv

# باید قبل از import بقیه ماژول‌ها باشد تا ADMIN_ID از .env خوانده شود
load_dotenv()

from telegram.ext import ApplicationBuilder

from handlers import register_all_handlers
from core.database import init_db
from core.database.connection import close_db
from core.config import get_admin_ids

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
LISTEN_PORT = os.getenv("PORT") or os.getenv("TELEGRAM_LISTENING_PORT", "8443")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def on_startup(app):
    # 🔥 متد امن حذف آپدیت‌های معلق (Safe Flush):
    # با این کار تمام پیام‌هایی که در زمان خاموش بودن ربات فرستاده شده‌اند کور می‌شوند
    try:
        updates = await app.bot.get_updates(offset=-1, timeout=1)
        if updates:
            await app.bot.get_updates(offset=updates[-1].update_id + 1, timeout=1)
        logger.info(
            "🗑️ Telegram pending updates successfully cleared via safe offset approach"
        )
    except Exception:
        logger.exception("Failed to flush pending updates smoothly")

    await init_db()
    admins = get_admin_ids()
    if admins:
        logger.info("Admin IDs loaded: %s", ", ".join(admins))
    else:
        logger.warning(
            "ADMIN_ID is not set — admin will NOT receive orders/payments. "
            "Use /myid in bot to get your Telegram ID."
        )
    logger.info("Database initialized")


async def on_shutdown(app):
    try:
        await close_db()
    except Exception:
        logger.exception("DB close failed")
    logger.info("Shutdown complete")


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN (or BOT_TOKEN) is not set in the environment."
        )

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    register_all_handlers(application)
    logger.info("Telegram VPN bot started in polling mode")

    # آپدیت‌های مجاز برای هندلرها
    allowed_updates = ["message", "edited_message", "callback_query"]

    # اجرای مستقیم روی حالت Polling بدون تداخل با وب‌هوک‌های قدیمی
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=allowed_updates,
    )


if __name__ == "__main__":
    main()
