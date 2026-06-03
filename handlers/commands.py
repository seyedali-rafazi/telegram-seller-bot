# handlers/commands.py

import os

from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv

from core.state_manager import clear_state
from core.keyboards import get_main_menu_keyboard, get_language_keyboard
from core.i18n import t
from core.database import (
    add_user,
    get_user_language,
    is_user_banned,
)

load_dotenv()
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_URL = os.getenv("CHANNEL_URL")


async def check_membership(bot, user_id):
    if not CHANNEL_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        pass
    return False


async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str | None = None):
    chat_id = str(update.effective_chat.id)
    if lang is None:
        lang = await get_user_language(chat_id)
    await update.message.reply_text(
        t(lang, "welcome"),
        reply_markup=get_main_menu_keyboard(lang),
    )
    await update.message.reply_text(
        t(lang, "choose_lang"),
        reply_markup=get_language_keyboard(),
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    username = update.effective_user.username if update.effective_user else None

    await add_user(chat_id, username)

    if await is_user_banned(chat_id):
        lang = await get_user_language(chat_id)
        await update.message.reply_text(t(lang, "banned"))
        return

    is_member = await check_membership(context.bot, chat_id)
    if not is_member:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = [[InlineKeyboardButton("📢 Join channel", url=CHANNEL_URL)]]
        await update.message.reply_text(
            "🛑 Please join our channel first, then send /start again.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    clear_state(chat_id)
    await send_welcome(update, context)
