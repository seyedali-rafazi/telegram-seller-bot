# handlers/vpn/user_menu.py

import os

from telegram import Update
from telegram.ext import ContextTypes

from core.i18n import t
from core.keyboards import (
    get_main_menu_keyboard,
    get_back_keyboard,
    get_plans_keyboard,
    get_support_keyboard,
    get_confirm_purchase_keyboard,
)
from core.state_manager import clear_state, set_state
from core.constants import (
    STATE_WALLET_AMOUNT,
    CARD_NUMBER,
    CARD_HOLDER,
)
from core.database import (
    get_user_language,
    is_user_banned,
    get_active_plans,
    get_wallet_balance,
    get_plan,
    get_user_info,
    get_active_subscriptions,
    get_setting,
)
async def _lang(update: Update) -> str:
    return await get_user_language(str(update.effective_chat.id))


async def _guard_banned(update: Update) -> bool:
    uid = str(update.effective_chat.id)
    if await is_user_banned(uid):
        lang = await _lang(update)
        await update.message.reply_text(t(lang, "banned"))
        return True
    return False


async def btn_buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return
    lang = await _lang(update)
    plans = await get_active_plans()
    if not plans:
        await update.message.reply_text(
            t(lang, "no_plans"), reply_markup=get_main_menu_keyboard(lang)
        )
        return
    await update.message.reply_text(
        t(lang, "plans_title"),
        reply_markup=get_plans_keyboard(plans, lang),
    )


async def btn_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return
    lang = await _lang(update)
    uid = str(update.effective_chat.id)
    info = await get_user_info(uid)
    if not info:
        await update.message.reply_text("/start")
        return

    username, _, join_date, _ = info
    username_str = f"@{username}" if username else "—"
    balance = await get_wallet_balance(uid)
    subs = await get_active_subscriptions(uid)

    if subs:
        lines = [
            t(lang, "service_line", name=s[1], expires=s[2][:10]) for s in subs
        ]
        services = "\n".join(lines)
    else:
        services = t(lang, "no_active_service")

    text = (
        t(lang, "account_title")
        + "\n\n"
        + t(
            lang,
            "account_body",
            uid=uid,
            username=username_str,
            balance=balance,
            join_date=join_date or "—",
            services=services,
        )
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(lang)
    )


async def btn_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return
    lang = await _lang(update)
    card = CARD_NUMBER or await get_setting("card_number", "")
    card_name = CARD_HOLDER or await get_setting("card_holder", "VPN")
    if not card:
        msg = (
            "⚠️ شماره کارت هنوز تنظیم نشده. با ادمین تماس بگیرید."
            if lang == "fa"
            else "⚠️ Card number not configured. Contact admin."
        )
        await update.message.reply_text(msg)
        return

    set_state(str(update.effective_chat.id), STATE_WALLET_AMOUNT)
    await update.message.reply_text(
        t(lang, "wallet_intro", card=card, card_name=card_name),
        parse_mode="Markdown",
        reply_markup=get_back_keyboard(lang),
    )


async def btn_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _guard_banned(update):
        return
    lang = await _lang(update)
    await update.message.reply_text(
        t(lang, "support_guide"),
        parse_mode="Markdown",
        reply_markup=get_support_keyboard(lang),
    )


async def btn_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await _lang(update)
    clear_state(str(update.effective_chat.id))
    await update.message.reply_text(
        t(lang, "welcome"),
        reply_markup=get_main_menu_keyboard(lang),
    )


def _matches_btn(text: str, key: str) -> bool:
    return text in (t("fa", key), t("en", key))


async def route_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if _matches_btn(text, "btn_buy"):
        await btn_buy_plan(update, context)
    elif _matches_btn(text, "btn_account"):
        await btn_account(update, context)
    elif _matches_btn(text, "btn_wallet"):
        await btn_wallet(update, context)
    elif _matches_btn(text, "btn_support"):
        await btn_support(update, context)
    elif _matches_btn(text, "btn_back"):
        await btn_back(update, context)
