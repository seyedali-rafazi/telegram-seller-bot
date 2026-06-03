# handlers/__init__.py

from telegram.ext import (
    MessageHandler,
    CommandHandler,
    filters,
    CallbackQueryHandler,
)

from .commands import cmd_start
from .vpn.user_menu import route_menu_button
from .vpn.callbacks import user_callback_router
from .vpn.states import process_wallet_state
from .admin.panel import cmd_admin, admin_callback, process_admin_state


def register_all_handlers(application):
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("admin", cmd_admin))

    application.add_handler(
        CallbackQueryHandler(
            user_callback_router,
            pattern=r"^(plan_|buy_confirm_|buy_cancel)",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern=r"^(adm_|pay_ok_|pay_no_|order_ok_|order_no_)",
        )
    )

    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            _text_router,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & (filters.PHOTO | filters.Document.ALL),
            _media_router,
        )
    )


async def _text_router(update, context):
    if await process_admin_state(update, context):
        return
    if await process_wallet_state(update, context):
        return
    await route_menu_button(update, context)


async def _media_router(update, context):
    if await process_admin_state(update, context):
        return
    if await process_wallet_state(update, context):
        return
