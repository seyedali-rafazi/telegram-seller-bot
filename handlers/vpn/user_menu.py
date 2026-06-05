# handlers/vpn/user_menu.py

from telegram import Update
from telegram.ext import ContextTypes

from core.messages import msg
from core.formatting import msg_e, h
from core.constants import (
    BTN_BUY,
    BTN_ACCOUNT,
    BTN_MY_ORDERS,
    BTN_WALLET,
    BTN_SUPPORT,
    BTN_BALE_SUB,
    BTN_TEST,
    BTN_BACK,
    STATE_WALLET_AMOUNT,
    STATE_BALE_ID,
    CARD_NUMBER,
    CARD_HOLDER,
)
from core.keyboards import (
    get_main_menu_keyboard,
    get_back_keyboard,
    get_plans_keyboard,
    get_support_keyboard,
)
from core.state_manager import clear_state, set_state
from core.database import (
    is_user_banned,
    get_active_plans,
    get_wallet_balance,
    get_user_info,
    get_active_subscriptions,
    get_user_pending_orders,
    get_setting,
    get_user_test_config,
    save_user_test_config,
)


async def _guard_banned(update: Update) -> bool:
    uid = str(update.effective_chat.id)
    if await is_user_banned(uid):
        await update.message.reply_text(msg("banned"))
        return True
    return False


async def btn_buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return
    plans = await get_active_plans()
    if not plans:
        await update.message.reply_text(
            msg("no_plans"), reply_markup=get_main_menu_keyboard()
        )
        return
    await update.message.reply_text(
        msg("plans_title"),
        reply_markup=get_plans_keyboard(plans),
    )


async def btn_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return
    uid = str(update.effective_chat.id)
    info = await get_user_info(uid)
    if not info:
        await update.message.reply_text("/start")
        return

    username, _, join_date, _ = info
    username_str = f"@{username}" if username else "—"
    balance = await get_wallet_balance(uid)
    pending = await get_user_pending_orders(uid)
    subs = await get_active_subscriptions(uid)

    if pending:
        pending_lines = [
            msg_e("order_pending_line", order_code=p[0], name=p[1], price=p[2])
            for p in pending
        ]
        pending_orders = "\n".join(pending_lines)
    else:
        pending_orders = msg("no_pending_orders")

    if subs:
        lines = [msg_e("service_line", name=s[1], expires=s[2][:10]) for s in subs]
        services = "\n".join(lines)
    else:
        services = msg("no_active_service")

    text = msg("account_title") + "\n\n" + msg(
        "account_body",
        uid=h(uid),
        username=h(username_str),
        balance=balance,
        join_date=h(join_date or "—"),
        pending_orders=pending_orders,
        services=services,
    )
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=get_main_menu_keyboard()
    )


async def btn_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return
    card = CARD_NUMBER or await get_setting("card_number", "")
    card_name = CARD_HOLDER or await get_setting("card_holder", "VPN")
    if not card:
        await update.message.reply_text(msg("card_not_set"))
        return

    set_state(str(update.effective_chat.id), STATE_WALLET_AMOUNT)
    await update.message.reply_text(
        msg_e("wallet_intro", card=card, card_name=card_name),
        parse_mode="HTML",
        reply_markup=get_back_keyboard(),
    )


async def btn_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return
    await update.message.reply_text(
        msg("support_guide"),
        parse_mode="HTML",
        reply_markup=get_support_keyboard(),
    )


async def btn_bale_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return
    set_state(str(update.effective_chat.id), STATE_BALE_ID)
    await update.message.reply_text(
        msg("bale_sub_ask_id"),
        parse_mode="HTML",
        reply_markup=get_back_keyboard(),
    )


async def btn_test_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return

    uid = str(update.effective_chat.id)
    existing = await get_user_test_config(uid)
    if existing:
        sub_url = existing[0]
        await update.message.reply_text(
            msg("test_config_already_used", sub_url=sub_url),
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    from services.xui_panel import (
        create_test_client,
        is_xui_configured,
        XuiPanelError,
        XuiPanelConnectionError,
    )

    if not is_xui_configured():
        await update.message.reply_text(
            msg("test_config_not_configured"),
            reply_markup=get_main_menu_keyboard(),
        )
        return

    wait_msg = await update.message.reply_text("⏳ در حال ساخت کانفیگ تست…")

    try:
        result = await create_test_client(uid)
    except XuiPanelConnectionError as exc:
        import logging

        logging.getLogger(__name__).error(
            "test config connection failed for %s: %s", uid, exc
        )
        await wait_msg.delete()
        await update.message.reply_text(
            msg("test_config_error"),
            reply_markup=get_main_menu_keyboard(),
        )
        return
    except XuiPanelError as exc:
        import logging

        logging.getLogger(__name__).error(
            "test config panel error for %s: %s", uid, exc
        )
        await wait_msg.delete()
        await update.message.reply_text(
            msg("test_config_error"),
            reply_markup=get_main_menu_keyboard(),
        )
        return
    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "test config creation failed for %s", uid
        )
        await wait_msg.delete()
        await update.message.reply_text(
            msg("test_config_error"),
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await save_user_test_config(
        uid,
        result["sub_url"],
        result["client_email"],
        result["sub_id"],
    )
    await wait_msg.delete()
    await update.message.reply_text(
        msg(
            "test_config_success",
            sub_url=result["sub_url"],
            traffic_mb=result["traffic_mb"],
        ),
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )


async def btn_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_state(str(update.effective_chat.id))
    await update.message.reply_text(
        msg("welcome"),
        reply_markup=get_main_menu_keyboard(),
    )


async def route_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_BUY:
        await btn_buy_plan(update, context)
    elif text == BTN_ACCOUNT:
        await btn_account(update, context)
    elif text == BTN_MY_ORDERS:
        from .user_orders_ui import btn_orders_hub

        await btn_orders_hub(update, context)
    elif text == BTN_WALLET:
        await btn_wallet(update, context)
    elif text == BTN_SUPPORT:
        await btn_support(update, context)
    elif text == BTN_BALE_SUB:
        await btn_bale_subscription(update, context)
    elif text == BTN_TEST:
        await btn_test_config(update, context)
    elif text == BTN_BACK:
        await btn_back(update, context)
