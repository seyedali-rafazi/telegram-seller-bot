# handlers/vpn/states.py

from telegram import Update
from telegram.ext import ContextTypes

from core.messages import msg
from core.state_manager import get_state, set_state, clear_state
from core.constants import (
    STATE_BALE_ID,
    STATE_PURCHASE_PROMO_CODE,
    STATE_PURCHASE_RECEIPT,
    BTN_BACK,
)
from core.keyboards import get_main_menu_keyboard, get_confirm_purchase_keyboard
from core.database import (
    create_bale_request,
    get_user_pending_bale_request,
    get_approved_history_by_bale_id,
    get_approved_history_by_user_id,
    build_bale_admin_history_text,
    validate_promo_code_for_purchase,
    get_plan,
    can_enter_promo_code,
)
from handlers.vpn.user_menu import btn_back
from handlers.vpn.callbacks import _confirm_text, submit_order_with_receipt


async def process_purchase_receipt_state(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    uid = str(update.effective_chat.id)
    state = get_state(uid)
    if state.get("step") != STATE_PURCHASE_RECEIPT:
        return False

    if update.message.text == BTN_BACK:
        clear_state(uid)
        await btn_back(update, context)
        return True

    photo = update.message.photo
    if not photo:
        await update.message.reply_text(msg("upload_receipt"))
        return True

    file_id = photo[-1].file_id
    return await submit_order_with_receipt(update, context, uid, file_id)


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

    pending = await get_user_pending_bale_request(uid)
    if pending:
        clear_state(uid)
        await update.message.reply_text(
            msg("bale_sub_pending_wait"),
            reply_markup=get_main_menu_keyboard(),
        )
        return True

    clear_state(uid)
    await update.message.reply_text(
        msg("bale_sub_received"),
        reply_markup=get_main_menu_keyboard(),
    )

    request = await create_bale_request(uid, bale_id)
    request_id = request["id"]
    request_code = request["public_id"]

    bale_history = await get_approved_history_by_bale_id(bale_id, exclude_request_id=request_id)
    user_history = await get_approved_history_by_user_id(uid, exclude_request_id=request_id)
    history_text = build_bale_admin_history_text(
        bale_history,
        user_history,
        current_bale_id=bale_id,
        current_user_id=uid,
    )

    from handlers.admin.user_panel import build_user_summary_text
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from core.admin_notify import notify_admins

    summary = await build_user_summary_text(uid)
    admin_text = (
        f"🔗 <b>درخواست اشتراک بله</b>\n\n"
        f"کد: <code>{request_code}</code>\n"
        f"🆔 شناسه بله: <code>{bale_id}</code>\n\n"
        f"{history_text}\n\n"
        f"{summary}"
    )
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📤 ارسال ساب",
                    callback_data=f"adm_bale_send_{request_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 پروفایل کاربر", callback_data=f"adm_uhome_{uid}"
                )
            ],
        ]
    )
    await notify_admins(context, text=admin_text, reply_markup=kb, parse_mode="HTML")
    return True


async def process_purchase_promo_state(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    uid = str(update.effective_chat.id)
    state = get_state(uid)
    if state.get("step") != STATE_PURCHASE_PROMO_CODE:
        return False

    text = (update.message.text or "").strip()
    plan_id = state.get("plan_id")
    plan = await get_plan(plan_id)
    if not plan or plan[5] != 1:
        clear_state(uid)
        await update.message.reply_text(msg("no_plans"))
        return True

    _, name, _, _, price, _ = plan
    show_promo = await can_enter_promo_code(uid)

    if text.lower() in ("/skip", "skip", "رد"):
        clear_state(uid)
        await update.message.reply_text(
            _confirm_text(name, price),
            reply_markup=get_confirm_purchase_keyboard(plan_id, show_promo=show_promo),
        )
        return True

    if text == BTN_BACK:
        clear_state(uid)
        await btn_back(update, context)
        return True

    ok, reason, owner_id = await validate_promo_code_for_purchase(uid, text)
    if not ok:
        if reason == "self":
            await update.message.reply_text(msg("promo_code_self"))
        elif reason == "not_first_buy":
            clear_state(uid)
            await update.message.reply_text(
                msg("promo_code_not_first_buy"),
                reply_markup=get_confirm_purchase_keyboard(plan_id, show_promo=False),
            )
        elif reason == "code_already_used":
            clear_state(uid)
            await update.message.reply_text(
                msg("promo_code_already_used"),
                reply_markup=get_confirm_purchase_keyboard(plan_id, show_promo=False),
            )
        else:
            await update.message.reply_text(msg("promo_code_invalid"))
        return True

    code = text.strip().upper()
    from core.state_manager import user_states

    user_states[uid] = {
        "plan_id": plan_id,
        "promo_code": code,
        "code_owner_id": owner_id,
    }
    await update.message.reply_text(
        msg("promo_code_applied", code=code),
        parse_mode="HTML",
    )
    await update.message.reply_text(
        _confirm_text(name, price, code),
        reply_markup=get_confirm_purchase_keyboard(plan_id, show_promo=show_promo),
    )
    return True
