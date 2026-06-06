# handlers/commands.py

import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from dotenv import load_dotenv

from core.state_manager import clear_state, set_state
from core.keyboards import get_main_menu_keyboard
from core.messages import msg
from core.config import is_admin_chat, get_admin_ids, get_primary_admin_id
from core.constants import STATE_ADMIN_USER_MESSAGE
from core.database import add_user, is_user_banned, user_exists, record_referral, qualify_referral, format_mb_display

load_dotenv()
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_URL = os.getenv("CHANNEL_URL")

ADMIN_HELP = """
📖 **راهنمای ادمین**

**دستورات:**
• `/admin` — باز کردن پنل مدیریت (دکمه‌های اینلاین)
• `/user 123456789` — پروفایل کاربر، سفارش‌های در انتظار، ارسال ساب
• `/message 123456789` — ارسال پیام به یک کاربر (متن در پیام بعدی)
• `/myid` — نمایش شناسه عددی تلگرام شما (برای قرار دادن در `.env`)
• `/help` — همین راهنما

**پنل `/admin`:**
• 👥 **کاربران** — لیست، مسدود/آزاد
• 🛒 **سفارش‌ها** — خرید پلن در انتظار
• 📦 **پلن‌ها** — افزودن / حذف پلن
• 🔗 **اشتراک بله** — درخواست‌های Pro بله → ارسال لینک Subscription
• 🔗 **ساب پولی / 🧪 ساب تست** — آپلود لینک‌های Subscription
• 📢 **پیام همگانی** — ارسال به همه کاربران
• 📊 **آمار**

**سفارش VPN (کارت به کارت):**
۱. کاربر پلن انتخاب می‌کند → واریز می‌کند → عکس رسید می‌فرستد
۲. شما عکس رسید + دکمه ✅/❌ دریافت می‌کنید
۳. **تأیید — ارسال ساب** → در پیام بعدی لینک Subscription بفرستید
۴. یا `/user شناسه` → **ارسال ساب** → هر سفارش معلق یک دکمه
۵. **رد** → سفارش لغو می‌شود

**اشتراک بله:**
۱. کاربر شناسه بله می‌فرستد → پیام با دکمه **📤 ارسال ساب** یا **❌ رد**
۲. لینک Subscription را در پیام بعدی بفرستید → برای کاربر ارسال می‌شود
۳. درخواست نامعتبر → **❌ رد** → کاربر می‌تواند دوباره درخواست دهد

**پیام به کاربر:**
• `/user شناسه` → **💬 پیام به کاربر** → متن را در پیام بعدی بفرستید
• یا `/message شناسه` (و در صورت نیاز متن در همان دستور)

**تنظیم `.env`:**
```
ADMIN_ID=شناسه_عددی_شما
CARD_NUMBER=شماره_کارت
CARD_HOLDER=نام_صاحب_کارت
```
چند ادمین: `ADMIN_IDS=111,222`
"""


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

    referrer_id = None
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            raw = arg[4:]
            if raw.isdigit() and raw != chat_id:
                referrer_id = raw

    is_new = not await user_exists(chat_id)
    await add_user(chat_id, username)

    if referrer_id and is_new:
        await record_referral(referrer_id, chat_id)

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

    rewarded = await qualify_referral(chat_id)
    if rewarded:
        inviter_id, reward_mb = rewarded
        from core.database import get_referral_stats

        stats = await get_referral_stats(inviter_id)
        try:
            await context.bot.send_message(
                chat_id=int(inviter_id),
                text=msg(
                    "referral_inviter_notify",
                    reward_mb=reward_mb,
                    available_display=format_mb_display(stats["available_mb"]),
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass

    clear_state(chat_id)
    await send_welcome(update, context)


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    admins = get_admin_ids()
    is_adm = str(uid) in admins
    extra = "\n\n✅ شما در لیست ادمین هستید." if is_adm else (
        "\n\n⚠️ این شماره را در `.env` به عنوان `ADMIN_ID` قرار دهید."
    )
    await update.message.reply_text(
        f"🆔 شناسه عددی شما:\n`{uid}`{extra}",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin_chat(update.effective_chat.id):
        await update.message.reply_text(
            "برای کاربران: از منوی ربات استفاده کنید.\n"
            "ادمین: دستور /admin"
        )
        return
    await update.message.reply_text(ADMIN_HELP.strip(), parse_mode="Markdown")


async def cmd_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin_chat(update.effective_chat.id):
        return
    if not context.args:
        await update.message.reply_text(
            "❌ فرمت:\n<code>/message 123456789</code>\n\n"
            "سپس متن پیام را در پیام بعدی ارسال کنید.\n"
            "یا: <code>/message 123456789 سلام، پیام شما</code>",
            parse_mode="HTML",
        )
        return

    user_id = context.args[0].strip()
    if not user_id.isdigit():
        await update.message.reply_text("❌ شناسه کاربر باید عدد باشد.")
        return

    if not await user_exists(user_id):
        await update.message.reply_text(
            f"❌ کاربر <code>{user_id}</code> در دیتابیس یافت نشد.",
            parse_mode="HTML",
        )
        return

    if len(context.args) >= 2:
        text = " ".join(context.args[1:])
        try:
            await context.bot.send_message(chat_id=int(user_id), text=text)
            await update.message.reply_text(
                msg("admin_message_sent", user_id=user_id),
                parse_mode="HTML",
            )
        except Exception:
            await update.message.reply_text(
                msg("admin_message_failed", user_id=user_id),
                parse_mode="HTML",
            )
        return

    set_state(get_primary_admin_id(), STATE_ADMIN_USER_MESSAGE, target_user=user_id)
    await update.message.reply_text(
        f"💬 متن پیام برای کاربر <code>{user_id}</code> را ارسال کنید:",
        parse_mode="HTML",
    )
