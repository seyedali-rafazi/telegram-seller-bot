# handlers/vpn/states.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.messages import msg
from core.admin_notify import notify_admins
from core.state_manager import get_state, set_state, clear_state
from core.constants import (
    STATE_WALLET_AMOUNT,
    STATE_WALLET_RECEIPT,
    STATE_BALE_ID,
    BTN_BACK,
)
from core.keyboards import get_main_menu_keyboard
from core.database import create_payment_request
from handlers.vpn.user_menu import btn_back


async def process_wallet_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    uid = str(update.effective_chat.id)
    state = get_state(uid)
    step = state.get("step")
    if not step:
        return False

    if update.message.text == BTN_BACK:
        clear_state(uid)
        await btn_back(update, context)
        return True

    if step == STATE_WALLET_AMOUNT:
        text = (update.message.text or "").strip().replace(",", "")
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text(msg("invalid_amount"))
            return True
        amount = int(text)
        set_state(uid, STATE_WALLET_RECEIPT, amount=amount)
        await update.message.reply_text(msg("upload_receipt"))
        return True

    if step == STATE_WALLET_RECEIPT:
        photo = update.message.photo
        if not photo:
            await update.message.reply_text(msg("upload_receipt"))
            return True

        amount = state.get("amount", 0)
        file_id = photo[-1].file_id
        payment = await create_payment_request(uid, amount, file_id)
        payment_id = payment["id"]
        payment_code = payment["public_id"]
        clear_state(uid)

        await update.message.reply_text(
            msg("receipt_submitted", payment_code=payment_code, amount=amount),
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(),
        )

        from core.database.users import get_user_info

        info = await get_user_info(uid)
        uname = info[0] if info else "—"
        caption = (
            f"💳 درخواست شارژ\n\n"
            f"کد: {payment_code}\n"
            f"شناسه دیتابیس: {payment_id}\n\n"
            f"کاربر: {uid} (@{uname})\n"
            f"مبلغ: {amount:,} تومان"
        )
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ تأیید", callback_data=f"pay_ok_{payment_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ رد", callback_data=f"pay_no_{payment_id}"
                    ),
                ]
            ]
        )
        await notify_admins(
            context,
            text=caption,
            photo_file_id=file_id,
            caption=caption,
            reply_markup=kb,
        )
        return True

    return False


async def process_bale_sub_state(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    uid = str(update.effective_chat.id)
    state = get_state(uid)
    if state.get("step") != STATE_BALE_ID:
        return False

    if update.message.text == BTN_BACK:
        clear_state(uid)
        await btn_back(update, context)
        return True

    bale_id = (update.message.text or "").strip()
    if not bale_id.isdigit():
        await update.message.reply_text(msg("bale_sub_invalid_id"))
        return True

    clear_state(uid)
    await update.message.reply_text(
        msg("bale_sub_received"),
        reply_markup=get_main_menu_keyboard(),
    )

    from handlers.admin.user_panel import build_user_summary_text

    summary = await build_user_summary_text(uid)
    admin_text = (
        f"🔗 <b>درخواست اشتراک بله</b>\n\n"
        f"🆔 شناسه بله: <code>{bale_id}</code>\n\n"
        f"{summary}"
    )
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👤 پروفایل کاربر", callback_data=f"adm_uhome_{uid}"
                )
            ]
        ]
    )
    await notify_admins(context, text=admin_text, reply_markup=kb, parse_mode="HTML")
    return True
