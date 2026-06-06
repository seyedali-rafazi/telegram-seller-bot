# handlers/vpn/referral.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.messages import msg
from core.formatting import msg_e, format_sub_delivery
from core.keyboards import get_main_menu_keyboard
from core.constants import REFERRAL_REWARD_MB, REFERRAL_CLAIM_MB
from core.database import (
    get_referral_stats,
    format_mb_display,
    claim_referral_internet,
)


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
        ok, reason, sub_url = await claim_referral_internet(uid)
        stats = await get_referral_stats(uid)
        if not ok:
            if reason == "insufficient":
                text = msg(
                    "referral_claim_insufficient",
                    claim_mb=REFERRAL_CLAIM_MB,
                    reward_mb=REFERRAL_REWARD_MB,
                    available_display=format_mb_display(stats["available_mb"]),
                    invite_count=stats["invite_count"],
                )
            elif reason == "empty_pool":
                text = msg("referral_claim_empty_pool")
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

        stats = await get_referral_stats(uid)
        text = msg(
            "referral_claim_ok",
            claim_mb=REFERRAL_CLAIM_MB,
            remaining_display=format_mb_display(stats["available_mb"]),
            sub_body=format_sub_delivery(sub_url),
        )
        await query.edit_message_text(
            text,
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
