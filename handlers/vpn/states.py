# handlers/vpn/states.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.messages import msg
from core.state_manager import get_state, set_state, clear_state
from core.constants import STATE_WALLET_AMOUNT, STATE_WALLET_RECEIPT, ADMIN_ID, BTN_BACK
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
        payment_id = await create_payment_request(uid, amount, file_id)
        clear_state(uid)

        await update.message.reply_text(
            msg("receipt_submitted", amount=amount),
            reply_markup=get_main_menu_keyboard(),
        )

        if ADMIN_ID:
            from core.database.users import get_user_info

            info = await get_user_info(uid)
            uname = info[0] if info else "—"
            caption = (
                f"💳 درخواست شارژ #{payment_id}\n"
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
            try:
                await context.bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=file_id,
                    caption=caption,
                    reply_markup=kb,
                )
            except Exception:
                pass
        return True

    return False
