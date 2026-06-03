# handlers/vpn/callbacks.py

from telegram import Update
from telegram.ext import ContextTypes

from core.i18n import t
from core.keyboards import (
    get_main_menu_keyboard,
    get_confirm_purchase_keyboard,
)
from core.database import (
    get_user_language,
    is_user_banned,
    set_user_language,
    get_plan,
    get_wallet_balance,
    purchase_plan,
)
async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    lang = "fa" if query.data == "lang_fa" else "en"
    await set_user_language(uid, lang)
    await query.edit_message_text(t(lang, "lang_set"))
    await context.bot.send_message(
        chat_id=uid,
        text=t(lang, "welcome"),
        reply_markup=get_main_menu_keyboard(lang),
    )


async def plan_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    if await is_user_banned(uid):
        return

    lang = await get_user_language(uid)
    plan_id = int(query.data.replace("plan_", ""))
    plan = await get_plan(plan_id)
    if not plan or plan[5] != 1:
        await query.edit_message_text(t(lang, "no_plans"))
        return

    _, name, _, _, price, _ = plan
    balance = await get_wallet_balance(uid)
    await query.edit_message_text(
        t(lang, "confirm_buy", name=name, price=price, balance=balance),
        reply_markup=get_confirm_purchase_keyboard(plan_id, lang),
    )


async def buy_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    lang = await get_user_language(uid)

    if query.data == "buy_cancel":
        await query.edit_message_text(t(lang, "welcome"))
        return

    plan_id = int(query.data.replace("buy_confirm_", ""))
    plan = await get_plan(plan_id)
    if not plan:
        await query.edit_message_text(t(lang, "no_plans"))
        return

    _, name, _, _, price, _ = plan
    balance = await get_wallet_balance(uid)

    ok, reason, extra = await purchase_plan(uid, plan_id)
    if not ok:
        if reason == "insufficient_balance":
            await query.edit_message_text(
                t(lang, "insufficient_balance", price=price, balance=balance)
            )
        elif reason == "no_config":
            await query.edit_message_text(t(lang, "no_configs"))
        else:
            await query.edit_message_text(t(lang, "no_plans"))
        return

    await query.edit_message_text("✅")
    await context.bot.send_message(
        chat_id=uid,
        text=t(
            lang,
            "purchase_ok",
            name=extra["name"],
            expires=extra["expires"],
            config=extra["config"],
        ),
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(lang),
    )


async def user_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data.startswith("lang_"):
        await language_callback(update, context)
    elif data.startswith("plan_"):
        await plan_select_callback(update, context)
    elif data.startswith("buy_confirm_") or data == "buy_cancel":
        await buy_confirm_callback(update, context)
