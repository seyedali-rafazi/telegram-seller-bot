# handlers/commands.py

import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from dotenv import load_dotenv

from core.state_manager import clear_state
from core.keyboards import get_main_menu_keyboard
from core.messages import msg
from core.config import is_admin_chat, get_admin_ids
from core.database import add_user, is_user_banned

load_dotenv()
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_URL = os.getenv("CHANNEL_URL")

ADMIN_HELP = """
📖 **راهنمای ادمین**

**دستورات:**
• `/admin` — باز کردن پنل مدیریت (دکمه‌های اینلاین)
• `/user 123456789` — پروفایل کاربر، سفارش‌های در انتظار، ارسال کانفیگ
• `/myid` — نمایش شناسه عددی تلگرام شما (برای قرار دادن در `.env`)
• `/help` — همین راهنما

**پنل `/admin`:**
• 👥 **کاربران** — لیست، تغییر موجودی، مسدود/آزاد
• 💳 **تأیید پرداخت‌ها** — درخواست‌های شارژ کیف پول
• 🛒 **سفارش‌ها** — خرید پلن در انتظار
• 📦 **پلن‌ها** — افزودن / حذف پلن
• 🔗 **کانفیگ‌ها** — ذخیره لیست لینک (اختیاری)
• 📢 **پیام همگانی** — ارسال به همه کاربران
• 📊 **آمار**

**شارژ کیف پول (کارت به کارت):**
۱. کاربر رسید می‌فرستد → شما عکس + دکمه ✅/❌ می‌گیرید
۲. **تأیید** → موجودی کاربر شارژ می‌شود
کد یکتا: `PAY-00000001`

**سفارش VPN:**
۱. کاربر پلن می‌خرد → پیام سفارش با کد `ORD-...`
۲. **تأیید — ارسال کانفیگ** → در پیام بعدی لینک VPN را بفرستید
۳. یا `/user شناسه` → **ارسال کانفیگ** → هر سفارش معلق یک دکمه → کلیک → لینک را بفرستید
۴. **سفارش‌های موفق** → مشاهده کانفیگی که قبلاً داده‌اید
۵. **رد** → سفارش لغو (بدون کسر وجه)

**تنظیم `.env`:**
```
ADMIN_ID=شناسه_عددی_شما
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
