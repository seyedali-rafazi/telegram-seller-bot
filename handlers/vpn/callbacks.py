# handlers/vpn/callbacks.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.messages import msg
from core.admin_notify import notify_admins
from core.keyboards import get_main_menu_keyboard, get_confirm_purchase_keyboard
from core.state_manager import get_state, set_state, clear_state
from core.constants import STATE_PURCHASE_PROMO_CODE
from core.database import (
    is_user_banned,
    get_plan,
    get_wallet_balance,
    create_purchase_order,
)
from core.database.users import get_user_info


def _confirm_text(name, price, balance, promo_code=None):
    if promo_code:
        return msg(
            "confirm_buy_with_code",
            name=name,
            price=price,
            balance=balance,
            promo_code=promo_code,
        )
    return msg("confirm_buy", name=name, price=price, balance=balance)


async def plan_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    if await is_user_banned(uid):
        return

    plan_id = int(query.data.replace("plan_", ""))
    plan = await get_plan(plan_id)
    if not plan or plan[5] != 1:
        await query.edit_message_text(msg("no_plans"))
        return

    _, name, _, _, price, _ = plan
    balance = await get_wallet_balance(uid)
    state = get_state(uid)
    promo_code = state.get("promo_code") if state.get("plan_id") == plan_id else None
    await query.edit_message_text(
        _confirm_text(name, price, balance, promo_code),
        reply_markup=get_confirm_purchase_keyboard(plan_id),
    )


async def _notify_admin_new_order(
    context,
    order_id,
    order_code,
    uid,
    name,
    price,
    duration_days,
    data_gb,
    invite_code=None,
):
    info = await get_user_info(uid)
    uname = info[0] if info else "—"
    text = (
        f"🛒 سفارش جدید\n\n"
        f"کد: {order_code}\n"
        f"شناسه دیتابیس: {order_id}\n\n"
        f"👤 کاربر: {uid} (@{uname})\n"
        f"📦 پلن: {name}\n"
        f"⏱ {duration_days} روز | 📊 {data_gb} گیگ\n"
        f"💰 {price:,} تومان"
    )
    if invite_code:
        text += f"\n🎫 کد دعوت: `{invite_code}`"
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ تأیید — ارسال کانفیگ",
                    callback_data=f"order_ok_{order_id}",
                )
            ],
            [InlineKeyboardButton("❌ رد سفارش", callback_data=f"order_no_{order_id}")],
        ]
    )
    await notify_admins(context, text, reply_markup=kb)


async def buy_promo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    plan_id = int(query.data.replace("buy_promo_", ""))
    set_state(uid, STATE_PURCHASE_PROMO_CODE, plan_id=plan_id)
    await query.edit_message_text(
        msg("promo_code_ask", skip_hint="`/skip`"),
        parse_mode="HTML",
    )


async def buy_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)

    if query.data == "buy_cancel":
        clear_state(uid)
        await query.edit_message_text(msg("welcome"))
        return

    plan_id = int(query.data.replace("buy_confirm_", ""))
    plan = await get_plan(plan_id)
    if not plan:
        await query.edit_message_text(msg("no_plans"))
        return

    _, name, _, _, price, _ = plan
    balance = await get_wallet_balance(uid)
    state = get_state(uid)
    promo_code = None
    code_owner_id = None
    if state.get("plan_id") == plan_id and state.get("promo_code"):
        promo_code = state["promo_code"]
        code_owner_id = state.get("code_owner_id")

    ok, reason, extra = await create_purchase_order(
        uid, plan_id, invite_code=promo_code, code_owner_id=code_owner_id
    )
    clear_state(uid)

    if not ok:
        if reason == "insufficient_balance":
            await query.edit_message_text(
                msg(
                    "insufficient_balance",
                    price=extra["price"] if extra else price,
                    balance=extra["balance"] if extra else balance,
                )
            )
        elif reason == "too_many_pending":
            await query.edit_message_text(
                msg("too_many_pending", count=extra.get("count", 5))
            )
        else:
            await query.edit_message_text(msg("no_plans"))
        return

    order_code = extra["public_id"]
    await query.edit_message_text(
        msg(
            "order_submitted",
            order_code=order_code,
            name=extra["name"],
            price=extra["price"],
            new_balance=extra["new_balance"],
        ),
        parse_mode="HTML",
    )
    await context.bot.send_message(
        chat_id=uid,
        text=msg("welcome"),
        reply_markup=get_main_menu_keyboard(),
    )
    await _notify_admin_new_order(
        context,
        extra["order_id"],
        order_code,
        uid,
        extra["name"],
        extra["price"],
        extra["duration_days"],
        extra["data_gb"],
        invite_code=promo_code,
    )


async def user_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data.startswith("plan_"):
        await plan_select_callback(update, context)
    elif data.startswith("buy_promo_"):
        await buy_promo_callback(update, context)
    elif data.startswith("buy_confirm_") or data == "buy_cancel":
        await buy_confirm_callback(update, context)
