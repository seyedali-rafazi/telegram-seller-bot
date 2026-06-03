import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from core.state_manager import set_state, get_state, clear_state
from core.keyboards import (
    get_yt_quality_telegram_keyboard,
    get_yt_delivery_keyboard,
    get_main_menu_keyboard,
)
from core.database import increment_yt_downloads
from services.youtube import get_video_filesize
from .task import background_yt_download


def _quality_prompt(format_type: str) -> str:
    if format_type == "audio":
        return "🎵 کیفیت صوت را انتخاب کنید (محدودیت: 2 گیگابایت):"
    return "🎥 کیفیت ویدیو را انتخاب کنید (محدودیت: 2 گیگابایت):"


async def youtube_delivery_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Error answering callback query: {e}")

    data = query.data
    chat_id = str(query.message.chat_id)

    if data not in ["ytdel_zip", "ytdel_video"]:
        return

    user_state = get_state(chat_id)
    if not user_state or user_state.get("step") != "waiting_yt_delivery":
        await query.edit_message_text(
            "❌ درخواست شما منقضی شده است. لطفا مجددا لینک را ارسال کنید."
        )
        return

    delivery_mode = "zip" if data == "ytdel_zip" else "video"
    url = user_state.get("yt_url")
    format_type = user_state.get("format")

    set_state(
        chat_id,
        "waiting_yt_quality",
        yt_url=url,
        format=format_type,
        delivery_mode=delivery_mode,
    )

    await query.edit_message_text(
        _quality_prompt(format_type),
        reply_markup=get_yt_quality_telegram_keyboard(),
    )


async def youtube_quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Error answering callback query: {e}")

    data = query.data
    chat_id = str(query.message.chat_id)

    if not data.startswith("ytqual_"):
        return

    quality = data.split("_")[1]

    user_state = get_state(chat_id)
    if not user_state or user_state.get("step") not in [
        "waiting_yt_quality",
        "processing_yt_quality",
    ]:
        await query.edit_message_text(
            "❌ درخواست شما منقضی شده است. لطفا مجددا لینک را ارسال کنید."
        )
        return

    if user_state.get("step") == "processing_yt_quality":
        await query.answer("⏳ در حال پردازش... لطفا صبر کنید.")
        return

    url = user_state.get("yt_url")
    format_type = user_state.get("format")
    delivery_mode = user_state.get("delivery_mode", "zip")

    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    set_state(
        chat_id,
        "processing_yt_quality",
        yt_url=url,
        format=format_type,
        delivery_mode=delivery_mode,
    )

    try:
        await query.edit_message_text(
            "⏳ در حال بررسی کیفیت، لطفا صبر کنید...", reply_markup=None
        )
    except Exception:
        pass

    try:
        if format_type == "video":
            estimated_size = await asyncio.to_thread(get_video_filesize, url, quality)
        else:
            estimated_size = await asyncio.to_thread(
                get_video_filesize, url, "bestaudio"
            )

        limit = 2 * 1024 * 1024 * 1024

        if estimated_size and estimated_size > limit:
            size_mb = round(estimated_size / (1024 * 1024), 1)
            msg = (
                f"❌ فایل حدود {size_mb} مگابایت است و بیشتر از 2 گیگابایت می‌باشد. "
                "لطفاً کیفیت پایین‌تری انتخاب کنید."
            )
            set_state(
                chat_id,
                "waiting_yt_quality",
                yt_url=url,
                format=format_type,
                delivery_mode=delivery_mode,
            )
            await query.edit_message_text(
                msg, reply_markup=get_yt_quality_telegram_keyboard()
            )
            return
    except Exception as e:
        print(f"⚠️ Error checking filesize: {e}")
        set_state(
            chat_id,
            "waiting_yt_quality",
            yt_url=url,
            format=format_type,
            delivery_mode=delivery_mode,
        )
        await query.edit_message_text(
            "⚠️ خطا در محاسبه حجم فایل. لطفا دوباره یک کیفیت انتخاب کنید.",
            reply_markup=get_yt_quality_telegram_keyboard(),
        )
        return

    await query.edit_message_text("✅ درخواست ثبت شد. در حال انتقال به صف دانلود...")

    clear_state(chat_id)

    await context.bot.send_message(
        chat_id=chat_id,
        text="🔙 بازگشت به منوی اصلی",
        reply_markup=get_main_menu_keyboard(),
    )

    await increment_yt_downloads(chat_id)

    asyncio.create_task(
        background_yt_download(
            context,
            url,
            chat_id,
            format_type,
            quality=quality,
            delivery_mode=delivery_mode,
        )
    )
