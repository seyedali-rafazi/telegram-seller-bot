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
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_URL") or os.getenv("TELEGRAM_WEBHOOK_URL")
LISTEN_PORT = os.getenv("PORT") or os.getenv("TELEGRAM_LISTENING_PORT", "8443")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def on_startup(app):
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
    logger.info("Telegram VPN bot started")

    port = int(LISTEN_PORT)
    webhook_url = WEBHOOK_BASE_URL
    if webhook_url and not webhook_url.rstrip("/").endswith(BOT_TOKEN):
        webhook_url = f"{webhook_url.rstrip('/')}/{BOT_TOKEN}"

    allowed_updates = ["message", "edited_message", "callback_query"]

    if webhook_url:
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=allowed_updates,
        )
    else:
        logger.info("WEBHOOK_URL not set — running in polling mode")
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=allowed_updates,
        )


if __name__ == "__main__":
    main()
