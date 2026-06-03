# handlers/commands.py

import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from dotenv import load_dotenv

from core.state_manager import clear_state
from core.keyboards import get_main_menu_keyboard
from core.messages import msg
from core.database import add_user, is_user_banned

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


async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        msg("welcome"),
        reply_markup=get_main_menu_keyboard(),
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    username = update.effective_user.username if update.effective_user else None

    await add_user(chat_id, username)

    if await is_user_banned(chat_id):
        await update.message.reply_text(msg("banned"))
        return

    is_member = await check_membership(context.bot, chat_id)
    if not is_member:
        keyboard = [
            [InlineKeyboardButton(msg("join_channel_btn"), url=CHANNEL_URL)]
        ]
        await update.message.reply_text(
            msg("channel_required"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    clear_state(chat_id)
    await send_welcome(update, context)
