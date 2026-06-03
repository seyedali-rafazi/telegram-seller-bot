from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import ContextTypes

from core.constants import SUPPORT_URL
from core.database import (
    get_user_info,
    get_yt_downloads,
    get_music_downloads,
    get_tt_downloads,
    get_archive_fetches_used,
    archive_limit_period_label,
)
from core.limits import get_limit


async def btn_support_req(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💬 ارتباط با پشتیبانی", url=SUPPORT_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "برای ارتباط با پشتیبانی، طرح پیشنهادات و گزارش مشکلات، روی دکمه زیر کلیک کنید:",
        reply_markup=reply_markup,
    )


async def btn_profile_req(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    user_info = await get_user_info(user_id)

    if not user_info:
        await update.message.reply_text(
            "❌ اطلاعات شما یافت نشد. لطفاً دستور /start را ارسال کنید."
        )
        return

    username, is_vip, join_date, vip_expire_date = user_info

    username_str = f"@{username}" if username else "ندارد"

    vip_status_text = "🆓 رایگان"
    vip_duration_text = ""

    if is_vip == 1:
        vip_status_text = "💎 ویژه (پرو)"
        if vip_expire_date:
            try:
                expire_dt = datetime.fromisoformat(vip_expire_date)
                now = datetime.now()

                if expire_dt > now:
                    remaining_time = expire_dt - now
                    remaining_days = remaining_time.days + 1
                    vip_duration_text = f"\n⏳ اعتبار اشتراک: $ {remaining_days} $ روز"
                else:
                    vip_duration_text = "\n⏳ اعتبار اشتراک: منقضی شده"

            except Exception as e:
                print(f"Error parsing date for user {user_id}: {e}")
                vip_duration_text = "\n⏳ اعتبار اشتراک: نامشخص (خطا)"

    yt_count = await get_yt_downloads(user_id)
    music_count = await get_music_downloads(user_id)
    tt_dl_count = await get_tt_downloads(user_id)
    arc_count = await get_archive_fetches_used(user_id)

    yt_limit = get_limit("youtube_download", is_vip)
    music_limit = get_limit("music_download", is_vip)
    tt_dl_limit = get_limit("tiktok_download", is_vip)
    arc_limit = get_limit("yt_archive", is_vip)
    arc_period = archive_limit_period_label(is_vip)

    profile_text = f"""
🪪 **مشخصات شما**
🆔 ایدی عددی: `{user_id}`
👤 یوزرنیم: {username_str}
📊 وضعیت اشتراک: {vip_status_text}{vip_duration_text}
📆 اولین استفاده: {join_date}

⏳ **مصرف امروز (به وقت ایران؛ ریست نیمه‌شب):**
• یوتیوب | دانلود: $ {yt_count} / {yt_limit} $
• موسیقی | دانلود: $ {music_count} / {music_limit} $
• تیک‌تاک | دانلود: $ {tt_dl_count} / {tt_dl_limit} $

📥 **کش یوتیوب (دریافت از آرشیو — {arc_period}):**
• $ {arc_count} / {arc_limit} $
"""

    await update.message.reply_text(profile_text.strip(), parse_mode="Markdown")
