# handlers/vpn/user_menu.py

from telegram import Update
from telegram.ext import ContextTypes

from core.messages import msg
from core.formatting import msg_e, h, format_sub_delivery
from core.constants import (
    BTN_BUY,
    BTN_ACCOUNT,
    BTN_MY_ORDERS,
    BTN_SUPPORT,
    BTN_BALE_SUB,
    BTN_TEST,
    BTN_REFERRAL,
    BTN_BACK,
    STATE_BALE_ID,
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
    get_user_info,
    get_active_subscriptions,
    get_user_pending_orders,
    get_user_test_config,
    assign_test_config_to_user,
    get_user_pending_bale_request,
)
from .referral import btn_referral, build_referral_section


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

    referral_section = await build_referral_section(uid)

    text = msg("account_title") + "\n\n" + msg(
        "account_body",
        uid=h(uid),
        username=h(username_str),
        join_date=h(join_date or "—"),
        referral_section=referral_section,
        pending_orders=pending_orders,
        services=services,
    )
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=get_main_menu_keyboard()
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
    uid = str(update.effective_chat.id)
    pending = await get_user_pending_bale_request(uid)
    if pending:
        await update.message.reply_text(
            msg("bale_sub_pending_wait"),
            reply_markup=get_main_menu_keyboard(),
        )
        return
    set_state(uid, STATE_BALE_ID)
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
        await update.message.reply_text(
            msg(
                "test_config_already_used",
                sub_body=format_sub_delivery(existing[0]),
            ),
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    sub_url = await assign_test_config_to_user(uid)
    if not sub_url:
        await update.message.reply_text(
            msg("test_config_empty"),
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        msg("test_config_success", sub_body=format_sub_delivery(sub_url)),
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
    elif text == BTN_SUPPORT:
        await btn_support(update, context)
    elif text == BTN_BALE_SUB:
        await btn_bale_subscription(update, context)
    elif text == BTN_TEST:
        await btn_test_config(update, context)
    elif text == BTN_REFERRAL:
        await btn_referral(update, context)
    elif text == BTN_BACK:
        await btn_back(update, context)
