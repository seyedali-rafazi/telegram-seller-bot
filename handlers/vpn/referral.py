# handlers/vpn/referral.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.messages import msg
from core.formatting import msg_e
from core.admin_notify import notify_admins
from core.constants import (
    REFERRAL_REWARD_MB,
    REFERRAL_CLAIM_MB,
    PROMO_CODE_REWARD_MB,
    PROMO_CODE_CLAIM_MB,
)
from core.database import (
    get_referral_stats,
    get_promo_code_stats,
    format_mb_display,
    create_referral_reward_request,
    get_user_pending_referral_request,
    get_invite_code,
    SOURCE_LINK,
    SOURCE_CODE,
)
from handlers.admin.user_panel import build_user_summary_text


def referral_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🌐 اینترنت رایگان (لینک)",
                    callback_data="ref_claim_link",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎫 اینترنت رایگان (کد)",
                    callback_data="ref_claim_code",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔗 لینک و کد دعوت",
                    callback_data="ref_link",
                )
            ],
        ]
    )


def _stats_block(link_stats: dict, code_stats: dict) -> str:
    return msg(
        "referral_stats_block",
        link_available=format_mb_display(link_stats["available_mb"]),
        code_available=format_mb_display(code_stats["available_mb"]),
    )


def _referral_section(link_stats: dict, code_stats: dict) -> str:
    return msg(
        "referral_section",
        invite_count=link_stats["invite_count"],
        link_available=format_mb_display(link_stats["available_mb"]),
        link_earned=format_mb_display(link_stats["earned_mb"]),
        code_use_count=code_stats["use_count"],
        code_available=format_mb_display(code_stats["available_mb"]),
        code_earned=format_mb_display(code_stats["earned_mb"]),
        invite_code=code_stats["invite_code"],
    )


async def build_referral_section(uid: str) -> str:
    link_stats = await get_referral_stats(uid)
    code_stats = await get_promo_code_stats(uid)
    return _referral_section(link_stats, code_stats)


async def _menu_text(uid: str) -> str:
    link_stats = await get_referral_stats(uid)
    code_stats = await get_promo_code_stats(uid)
    return msg(
        "referral_menu",
        reward_mb=REFERRAL_REWARD_MB,
        claim_mb=REFERRAL_CLAIM_MB,
        promo_reward_mb=PROMO_CODE_REWARD_MB,
        invite_code=code_stats["invite_code"],
        stats_block=_stats_block(link_stats, code_stats),
    )


async def btn_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_chat.id)
    await update.message.reply_text(
        await _menu_text(uid),
        parse_mode="HTML",
        reply_markup=referral_menu_keyboard(),
    )


async def _submit_claim(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    uid: str,
    source: str,
) -> None:
    query = update.callback_query
    pending = await get_user_pending_referral_request(uid, source=source)
    if pending:
        await query.edit_message_text(
            msg("referral_claim_pending"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="ref_back")]]
            ),
        )
        return

    ok, reason, extra = await create_referral_reward_request(uid, source=source)
    link_stats = await get_referral_stats(uid)
    code_stats = await get_promo_code_stats(uid)
    stats = link_stats if source == SOURCE_LINK else code_stats
    source_label = extra["source_label"] if extra else (
        "لینک دعوت" if source == SOURCE_LINK else "کد دعوت"
    )
    min_mb = REFERRAL_CLAIM_MB if source == SOURCE_LINK else PROMO_CODE_CLAIM_MB

    if not ok:
        if reason == "insufficient":
            if source == SOURCE_LINK:
                text = msg(
                    "referral_claim_insufficient_link",
                    claim_mb=min_mb,
                    reward_mb=REFERRAL_REWARD_MB,
                    available_display=format_mb_display(
                        extra.get("available_mb", stats["available_mb"])
                        if extra
                        else stats["available_mb"]
                    ),
                    invite_count=link_stats["invite_count"],
                )
            else:
                text = msg(
                    "referral_claim_insufficient",
                    source_label=source_label,
                    claim_mb=min_mb,
                    available_display=format_mb_display(
                        extra.get("available_mb", stats["available_mb"])
                        if extra
                        else stats["available_mb"]
                    ),
                )
        elif reason == "pending_exists":
            text = msg("referral_claim_pending")
        else:
            text = "❌ خطا. /start را بزنید."
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="ref_back")]]
            ),
        )
        return

    request_id = extra["id"]
    request_code = extra["public_id"]
    mb_display = extra["mb_display"]
    summary = await build_user_summary_text(uid)
    admin_text = (
        f"🎁 <b>درخواست اینترنت رایگان</b>\n\n"
        f"نوع: <b>{source_label}</b>\n"
        f"کد: <code>{request_code}</code>\n"
        f"حجم: <b>{mb_display}</b>\n\n"
        f"{summary}"
    )
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📤 ارسال ساب",
                    callback_data=f"adm_refreq_send_{request_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ رد",
                    callback_data=f"adm_refreq_reject_{request_id}",
                ),
                InlineKeyboardButton(
                    "👤 پروفایل",
                    callback_data=f"adm_uhome_{uid}",
                ),
            ],
        ]
    )
    await notify_admins(context, text=admin_text, reply_markup=kb, parse_mode="HTML")

    await query.edit_message_text(
        msg(
            "referral_claim_submitted",
            request_code=request_code,
            mb_display=mb_display,
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 بازگشت", callback_data="ref_back")]]
        ),
    )


async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    data = query.data

    if data == "ref_link":
        me = await context.bot.get_me()
        link = f"https://t.me/{me.username}?start=ref_{uid}"
        invite_code = await get_invite_code(uid)
        await query.edit_message_text(
            msg_e(
                "referral_link",
                link=link,
                invite_code=invite_code,
                promo_reward_mb=PROMO_CODE_REWARD_MB,
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="ref_back")]]
            ),
        )
        return

    if data == "ref_claim_link":
        await _submit_claim(update, context, uid, SOURCE_LINK)
        return

    if data == "ref_claim_code":
        await _submit_claim(update, context, uid, SOURCE_CODE)
        return

    if data == "ref_back":
        await query.edit_message_text(
            await _menu_text(uid),
            parse_mode="HTML",
            reply_markup=referral_menu_keyboard(),
        )
