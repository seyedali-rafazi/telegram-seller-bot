# handlers/states/__init__.py

import time

from telegram import Update
from telegram.ext import ContextTypes
from core.state_manager import get_state
from .youtube import handle_youtube_state
from .state_insta import handle_insta_state
from .state_music import handle_music_state, handle_music_identify_media
from .state_tiktok import handle_tiktok_state
from .state_yt_archive import handle_yt_archive_search_state

_MENU_HINT_COOLDOWN_SEC = 3.0
_last_menu_hint_at: dict[str, float] = {}

_BOT_OWN_REPLIES = frozenset(
    {
        "لطفاً از منو استفاده کنید.",
        "متوجه نشدم. لطفاً از منو استفاده کنید.",
    }
)


def _is_human_message(update: Update) -> bool:
    chat = update.effective_chat
    if chat is None or chat.type != "private":
        return False
    user = update.effective_user
    if user is None or user.is_bot:
        return False
    if update.message is None:
        return False
    return True


async def _reply_menu_hint(
    update: Update,
    text: str = "لطفاً از منو استفاده کنید.",
) -> None:
    chat_id = str(update.effective_chat.id)
    now = time.monotonic()
    if now - _last_menu_hint_at.get(chat_id, 0.0) < _MENU_HINT_COOLDOWN_SEC:
        return
    _last_menu_hint_at[chat_id] = now
    await update.message.reply_text(text)


async def process_state_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_human_message(update):
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    if text.startswith("/"):
        return

    if text in _BOT_OWN_REPLIES:
        return

    chat_id = str(update.effective_chat.id)
    state_data = get_state(chat_id)
    step = state_data.get("step")

    if text in ["0", "لغو", "شروع"]:
        from handlers.commands import cmd_start

        await cmd_start(update, context)
        return

    if not step:
        await _reply_menu_hint(update)
        return

    if step.startswith("waiting_yt_archive_"):
        await handle_yt_archive_search_state(
            update, context, step, text, chat_id
        )
        return

    if step.startswith("waiting_yt"):
        await handle_youtube_state(update, context, step, text, chat_id, state_data)

    elif step.startswith("waiting_ig"):
        await handle_insta_state(update, context, step, text, chat_id, state_data)

    elif step in ["waiting_music_search", "waiting_spotify_link"]:
        await handle_music_state(update, context, step, text, chat_id, state_data)

    elif step.startswith("waiting_music_"):
        await handle_music_state(update, context, step, text, chat_id, state_data)

    elif step.startswith("waiting_tt"):
        await handle_tiktok_state(update, context, step, text, chat_id, state_data)


async def process_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_human_message(update):
        return

    await _reply_menu_hint(
        update, "متوجه نشدم. لطفاً از منو استفاده کنید."
    )


async def process_media_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_human_message(update):
        return

    chat_id = str(update.effective_chat.id)
    state_data = get_state(chat_id)
    step = state_data.get("step") if state_data else None

    if step == "waiting_music_identify":
        await handle_music_identify_media(update, context)
    else:
        await _reply_menu_hint(
            update, "متوجه نشدم. لطفاً از منو استفاده کنید."
        )
