# handlers/vpn/referral.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.messages import msg
from core.formatting import msg_e
from core.admin_notify import notify_admins
from core.constants import REFERRAL_REWARD_MB, REFERRAL_CLAIM_MB
from core.database import (
    get_referral_stats,
    format_mb_display,
    create_referral_reward_request,
    get_user_pending_referral_request,
)
from handlers.admin.user_panel import build_user_summary_text


def referral_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🌐 دریافت اینترنت رایگان",
                    callback_data="ref_claim",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔗 دریافت لینک دعوت",
                    callback_data="ref_link",
                )
            ],
        ]
    )


def _stats_block(stats: dict) -> str:
    return msg(
        "referral_stats_block",
        invite_count=stats["invite_count"],
        available_display=format_mb_display(stats["available_mb"]),
        earned_display=format_mb_display(stats["earned_mb"]),
    )


def _referral_section(stats: dict) -> str:
    return msg(
        "referral_section",
        invite_count=stats["invite_count"],
        earned_display=format_mb_display(stats["earned_mb"]),
        claimed_display=format_mb_display(stats["claimed_mb"]),
        available_display=format_mb_display(stats["available_mb"]),
    )


async def build_referral_section(uid: str) -> str:
    stats = await get_referral_stats(uid)
    return _referral_section(stats)


async def btn_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_chat.id)
    stats = await get_referral_stats(uid)
    text = msg(
        "referral_menu",
        reward_mb=REFERRAL_REWARD_MB,
        claim_mb=REFERRAL_CLAIM_MB,
        stats_block=_stats_block(stats),
    )
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=referral_menu_keyboard(),
    )


async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    data = query.data

    if data == "ref_link":
        me = await context.bot.get_me()
        link = f"https://t.me/{me.username}?start=ref_{uid}"
        await query.edit_message_text(
            msg_e("referral_link", link=link),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="ref_back")]]
            ),
        )
        return

    if data == "ref_claim":
        pending = await get_user_pending_referral_request(uid)
        if pending:
            await query.edit_message_text(
                msg("referral_claim_pending"),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data="ref_back")]]
                ),
            )
            return

        ok, reason, extra = await create_referral_reward_request(uid)
        stats = await get_referral_stats(uid)
        if not ok:
            if reason == "insufficient":
                text = msg(
                    "referral_claim_insufficient",
                    claim_mb=REFERRAL_CLAIM_MB,
                    reward_mb=REFERRAL_REWARD_MB,
                    available_display=format_mb_display(
                        extra.get("available_mb", stats["available_mb"])
                        if extra
                        else stats["available_mb"]
                    ),
                    invite_count=stats["invite_count"],
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
            f"🎁 <b>درخواست اینترنت رایگان (دعوت)</b>\n\n"
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
                        "❌ رد درخواست",
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
        return

    if data == "ref_back":
        stats = await get_referral_stats(uid)
        text = msg(
            "referral_menu",
            reward_mb=REFERRAL_REWARD_MB,
            claim_mb=REFERRAL_CLAIM_MB,
            stats_block=_stats_block(stats),
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=referral_menu_keyboard(),
        )
