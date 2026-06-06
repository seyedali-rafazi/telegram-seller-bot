# handlers/vpn/callbacks.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.messages import msg
from core.admin_notify import notify_admins
from core.keyboards import get_main_menu_keyboard, get_confirm_purchase_keyboard, get_back_keyboard
from core.state_manager import get_state, set_state, clear_state
from core.constants import (
    STATE_PURCHASE_PROMO_CODE,
    STATE_PURCHASE_RECEIPT,
    CARD_NUMBER,
    CARD_HOLDER,
)
from core.formatting import msg_e
from core.database import (
    is_user_banned,
    get_plan,
    create_purchase_order,
    can_enter_promo_code,
    get_setting,
)
from core.database.orders import count_user_pending_orders, MAX_PENDING_ORDERS_PER_USER
from core.database.users import get_user_info


def _confirm_text(name, price, promo_code=None):
    if promo_code:
        return msg(
            "confirm_buy_with_code",
            name=name,
            price=price,
            promo_code=promo_code,
        )
    return msg("confirm_buy", name=name, price=price)


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
    state = get_state(uid)
    promo_code = state.get("promo_code") if state.get("plan_id") == plan_id else None
    show_promo = await can_enter_promo_code(uid)
    await query.edit_message_text(
        _confirm_text(name, price, promo_code),
        reply_markup=get_confirm_purchase_keyboard(plan_id, show_promo=show_promo),
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
    receipt_file_id,
    invite_code=None,
):
    info = await get_user_info(uid)
    uname = info[0] if info else "—"
    caption = (
        f"🛒 سفارش جدید\n\n"
        f"کد: {order_code}\n"
        f"شناسه دیتابیس: {order_id}\n\n"
        f"👤 کاربر: {uid} (@{uname})\n"
        f"📦 پلن: {name}\n"
        f"⏱ {duration_days} روز | 📊 {data_gb} گیگ\n"
        f"💰 {price:,} تومان"
    )
    if invite_code:
        caption += f"\n🎫 کد دعوت: `{invite_code}`"
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ تأیید — ارسال ساب",
                    callback_data=f"order_ok_{order_id}",
                )
            ],
            [InlineKeyboardButton("❌ رد سفارش", callback_data=f"order_no_{order_id}")],
        ]
    )
    await notify_admins(
        context,
        text=caption,
        photo_file_id=receipt_file_id,
        caption=caption,
        reply_markup=kb,
    )


async def buy_promo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    if not await can_enter_promo_code(uid):
        await query.answer("کد دعوت فقط برای اولین خرید است.", show_alert=True)
        return
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
    state = get_state(uid)
    promo_code = None
    code_owner_id = None
    if state.get("plan_id") == plan_id and state.get("promo_code"):
        promo_code = state["promo_code"]
        code_owner_id = state.get("code_owner_id")

    pending_n = await count_user_pending_orders(uid)
    if pending_n >= MAX_PENDING_ORDERS_PER_USER:
        await query.edit_message_text(
            msg("too_many_pending", count=pending_n)
        )
        return

    card = CARD_NUMBER or await get_setting("card_number", "")
    card_name = CARD_HOLDER or await get_setting("card_holder", "VPN")
    if not card:
        clear_state(uid)
        await query.edit_message_text(msg("card_not_set"))
        return

    set_state(
        uid,
        STATE_PURCHASE_RECEIPT,
        plan_id=plan_id,
        promo_code=promo_code,
        code_owner_id=code_owner_id,
    )
    await query.edit_message_text(
        msg_e(
            "buy_pay_instructions",
            price=price,
            name=name,
            card=card,
            card_name=card_name,
        ),
        parse_mode="HTML",
    )
    await context.bot.send_message(
        chat_id=uid,
        text=msg("upload_receipt"),
        reply_markup=get_back_keyboard(),
    )


async def submit_order_with_receipt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    uid: str,
    receipt_file_id: str,
) -> bool:
    state = get_state(uid)
    if state.get("step") != STATE_PURCHASE_RECEIPT:
        return False

    plan_id = state.get("plan_id")
    promo_code = state.get("promo_code")
    code_owner_id = state.get("code_owner_id")

    ok, reason, extra = await create_purchase_order(
        uid,
        plan_id,
        receipt_file_id,
        invite_code=promo_code,
        code_owner_id=code_owner_id,
    )
    clear_state(uid)

    if not ok:
        if reason == "too_many_pending":
            await update.message.reply_text(
                msg("too_many_pending", count=extra.get("count", 5)),
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            await update.message.reply_text(
                msg("no_plans"),
                reply_markup=get_main_menu_keyboard(),
            )
        return True

    order_code = extra["public_id"]
    await update.message.reply_text(
        msg(
            "order_submitted",
            order_code=order_code,
            name=extra["name"],
            price=extra["price"],
        ),
        parse_mode="HTML",
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
        receipt_file_id,
        invite_code=promo_code,
    )
    return True


async def user_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data.startswith("plan_"):
        await plan_select_callback(update, context)
    elif data.startswith("buy_promo_"):
        await buy_promo_callback(update, context)
    elif data.startswith("buy_confirm_") or data == "buy_cancel":
        await buy_confirm_callback(update, context)
