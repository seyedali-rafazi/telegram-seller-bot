# handlers/__init__.py

from telegram.ext import (
    MessageHandler,
    CommandHandler,
    filters,
    CallbackQueryHandler,
)

from .commands import cmd_start, cmd_myid, cmd_help, cmd_message
from .vpn.user_menu import route_menu_button
from .vpn.callbacks import user_callback_router
from .vpn.states import process_purchase_receipt_state, process_bale_sub_state, process_purchase_promo_state
from .admin.panel import cmd_admin, admin_callback, process_admin_state
from .admin.user_panel import cmd_user
from .vpn.user_orders_ui import user_orders_callback
from .vpn.referral import referral_callback


def register_all_handlers(application):
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("admin", cmd_admin))
    application.add_handler(CommandHandler("myid", cmd_myid))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("message", cmd_message))
    application.add_handler(CommandHandler("user", cmd_user))

    application.add_handler(
        CallbackQueryHandler(
            user_callback_router,
            pattern=r"^(plan_|buy_confirm_|buy_cancel|buy_promo_)",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            referral_callback,
            pattern=r"^ref_",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            user_orders_callback,
            pattern=r"^usr_",
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
    if await process_purchase_receipt_state(update, context):
        return
    if await process_bale_sub_state(update, context):
        return
    if await process_purchase_promo_state(update, context):
        return
    await route_menu_button(update, context)


async def _media_router(update, context):
    if await process_admin_state(update, context):
        return
    if await process_purchase_receipt_state(update, context):
        return
