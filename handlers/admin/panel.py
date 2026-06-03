# handlers/admin/panel.py

import asyncio
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.constants import ADMIN_ID
from core.keyboards import get_admin_menu_keyboard
from core.state_manager import set_state, clear_state, get_state
from core.constants import (
    STATE_ADMIN_BROADCAST,
    STATE_ADMIN_CONFIGS,
    STATE_ADMIN_PLAN_NAME,
    STATE_ADMIN_PLAN_DAYS,
    STATE_ADMIN_PLAN_GB,
    STATE_ADMIN_PLAN_PRICE,
    STATE_ADMIN_USER_BALANCE,
)
from core.database import (
    get_total_users,
    count_pending_payments,
    get_pending_payments,
    get_all_plans,
    count_available_configs,
    count_total_configs,
    get_all_users,
    approve_payment,
    reject_payment,
    get_payment,
    add_configs_bulk,
    create_plan,
    delete_plan,
    update_plan,
    search_users_page,
    set_wallet_balance,
    adjust_wallet,
    set_user_banned,
    get_wallet_balance,
)
from core.database.users import get_user_info


def is_admin(update: Update) -> bool:
    return str(update.effective_chat.id) == ADMIN_ID


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    pending = await count_pending_payments()
    avail = await count_available_configs()
    await update.message.reply_text(
        f"🛠 **پنل ادمین**\n\n"
        f"پرداخت‌های در انتظار: {pending}\n"
        f"کانفیگ آماده: {avail}\n\n"
        "گزینه را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_keyboard(),
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if str(query.message.chat_id) != ADMIN_ID:
        await query.answer()
        return

    await query.answer()
    data = query.data

    if data == "adm_stats":
        total = await get_total_users()
        pending = await count_pending_payments()
        avail = await count_available_configs()
        total_cfg = await count_total_configs()
        await query.edit_message_text(
            f"📊 آمار\n\n"
            f"کاربران: {total}\n"
            f"پرداخت معلق: {pending}\n"
            f"کانفیگ: {avail} آزاد / {total_cfg} کل"
        )
        return

    if data == "adm_payments":
        rows = await get_pending_payments(15)
        if not rows:
            await query.edit_message_text("✅ پرداخت معلقی نیست.")
            return
        lines = ["💳 **پرداخت‌های در انتظار:**\n"]
        for r in rows:
            lines.append(f"#{r[0]} — کاربر {r[1]} — {r[2]:,} تومان")
        lines.append("\nاز پیام‌های قبلی با دکمه تأیید/رد اقدام کنید.")
        await query.edit_message_text("\n".join(lines), parse_mode="Markdown")
        return

    if data == "adm_plans":
        plans = await get_all_plans()
        lines = ["📦 **پلن‌ها:**\n"]
        kb = []
        for p in plans:
            status = "✅" if p[5] else "❌"
            lines.append(
                f"{status} #{p[0]} {p[1]} — {p[2]}روز / {p[3]}GB — {p[4]:,}ت"
            )
            kb.append(
                [
                    InlineKeyboardButton(
                        f"🗑 حذف #{p[0]}", callback_data=f"adm_delplan_{p[0]}"
                    )
                ]
            )
        kb.append(
            [InlineKeyboardButton("➕ پلن جدید", callback_data="adm_addplan")]
        )
        kb.append(
            [InlineKeyboardButton("🔙 پنل", callback_data="adm_back")]
        )
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    if data == "adm_addplan":
        set_state(ADMIN_ID, STATE_ADMIN_PLAN_NAME)
        await query.edit_message_text("نام پلن را ارسال کنید (مثال: 1 Month - 30GB):")
        return

    if data.startswith("adm_delplan_"):
        pid = int(data.replace("adm_delplan_", ""))
        await delete_plan(pid)
        await query.edit_message_text(f"✅ پلن #{pid} حذف شد.")
        return

    if data == "adm_configs":
        set_state(ADMIN_ID, STATE_ADMIN_CONFIGS)
        avail = await count_available_configs()
        await query.edit_message_text(
            f"🔗 کانفیگ آزاد: {avail}\n\n"
            "لیست کانفیگ‌ها را ارسال کنید (هر خط یک لینک VLESS/vmess):\n"
            "یا فایل .txt آپلود کنید."
        )
        return

    if data == "adm_broadcast":
        set_state(ADMIN_ID, STATE_ADMIN_BROADCAST)
        await query.edit_message_text("📢 متن پیام همگانی را ارسال کنید:")
        return

    if data == "adm_users":
        rows = await search_users_page(0, 10)
        lines = ["👥 **کاربران (۱۰ نفر اخیر):**\n"]
        kb = []
        for r in rows:
            ban = "🚫" if r[3] else "✅"
            lines.append(
                f"{ban} `{r[0]}` @{r[1] or '—'} — {r[2]:,}ت"
            )
            kb.append(
                [
                    InlineKeyboardButton(
                        f"💰 {r[0][-6:]}",
                        callback_data=f"adm_wallet_{r[0]}",
                    ),
                    InlineKeyboardButton(
                        "🚫" if not r[3] else "✅",
                        callback_data=f"adm_ban_{r[0]}",
                    ),
                ]
            )
        kb.append([InlineKeyboardButton("🔙 پنل", callback_data="adm_back")])
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    if data == "adm_back":
        clear_state(ADMIN_ID)
        pending = await count_pending_payments()
        avail = await count_available_configs()
        await query.edit_message_text(
            f"🛠 پنل ادمین\nپرداخت معلق: {pending} | کانفیگ: {avail}",
            reply_markup=get_admin_menu_keyboard(),
        )
        return

    if data.startswith("adm_wallet_"):
        uid = data.replace("adm_wallet_", "")
        set_state(ADMIN_ID, STATE_ADMIN_USER_BALANCE, target_user=uid)
        bal = await get_wallet_balance(uid)
        await query.edit_message_text(
            f"کاربر {uid}\nموجودی: {bal:,}\n\n"
            "مبلغ جدید را بفرستید یا `+50000` / `-10000` برای افزایش/کاهش:"
        )
        return

    if data.startswith("adm_ban_"):
        uid = data.replace("adm_ban_", "")
        from core.database.users import is_user_banned

        banned = await is_user_banned(uid)
        await set_user_banned(uid, not banned)
        await query.answer("✅ وضعیت مسدودیت تغییر کرد", show_alert=True)
        return

    if data.startswith("pay_ok_"):
        pid = int(data.replace("pay_ok_", ""))
        ok, result = await approve_payment(pid)
        if ok:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ تأیید شد — کیف پول شارژ شد.",
                reply_markup=None,
            )
            try:
                await context.bot.send_message(
                    chat_id=result,
                    text=f"✅ پرداخت #{pid} تأیید شد. کیف پول شما شارژ شد.",
                )
            except Exception:
                pass
        else:
            await query.answer("خطا یا قبلاً بررسی شده", show_alert=True)
        return

    if data.startswith("pay_no_"):
        pid = int(data.replace("pay_no_", ""))
        payment = await get_payment(pid)
        ok = await reject_payment(pid)
        if ok and payment:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ رد شد.",
                reply_markup=None,
            )
            try:
                await context.bot.send_message(
                    chat_id=payment["user_id"],
                    text=f"❌ پرداخت #{pid} رد شد. با پشتیبانی تماس بگیرید.",
                )
            except Exception:
                pass
        return


async def process_admin_state(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    if str(update.effective_chat.id) != ADMIN_ID:
        return False

    state = get_state(ADMIN_ID)
    step = state.get("step")
    if not step:
        return False

    text = (update.message.text or "").strip()

    if step == STATE_ADMIN_BROADCAST:
        clear_state(ADMIN_ID)
        users = await get_all_users()
        await update.message.reply_text(f"⏳ ارسال به {len(users)} کاربر...")
        ok, fail = 0, 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=text)
                ok += 1
            except Exception:
                fail += 1
            await asyncio.sleep(0.05)
        await update.message.reply_text(f"✅ تمام — موفق: {ok} | ناموفق: {fail}")
        return True

    if step == STATE_ADMIN_CONFIGS:
        clear_state(ADMIN_ID)
        if update.message.document:
            doc = await update.message.document.get_file()
            content = (await doc.download_as_bytearray()).decode(
                "utf-8", errors="ignore"
            )
            lines = content.splitlines()
        else:
            lines = text.splitlines()
        added = await add_configs_bulk(lines)
        avail = await count_available_configs()
        await update.message.reply_text(
            f"✅ {added} کانفیگ اضافه شد.\nکانفیگ آزاد: {avail}"
        )
        return True

    if step == STATE_ADMIN_PLAN_NAME:
        set_state(ADMIN_ID, STATE_ADMIN_PLAN_DAYS, plan_name=text)
        await update.message.reply_text("تعداد روز (عدد):")
        return True

    if step == STATE_ADMIN_PLAN_DAYS:
        if not text.isdigit():
            await update.message.reply_text("عدد وارد کنید:")
            return True
        set_state(ADMIN_ID, STATE_ADMIN_PLAN_GB, plan_name=state["plan_name"], days=int(text))
        await update.message.reply_text("حجم GB (عدد):")
        return True

    if step == STATE_ADMIN_PLAN_GB:
        if not text.isdigit():
            await update.message.reply_text("عدد وارد کنید:")
            return True
        set_state(
            ADMIN_ID,
            STATE_ADMIN_PLAN_PRICE,
            plan_name=state["plan_name"],
            days=state["days"],
            data_gb=int(text),
        )
        await update.message.reply_text("قیمت به تومان (عدد):")
        return True

    if step == STATE_ADMIN_PLAN_PRICE:
        if not text.isdigit():
            await update.message.reply_text("عدد وارد کنید:")
            return True
        clear_state(ADMIN_ID)
        pid = await create_plan(
            state["plan_name"], state["days"], state["data_gb"], int(text)
        )
        await update.message.reply_text(f"✅ پلن #{pid} ایجاد شد.")
        return True

    if step == STATE_ADMIN_USER_BALANCE:
        uid = state.get("target_user")
        clear_state(ADMIN_ID)
        if text.startswith("+") or text.startswith("-"):
            delta = int(text)
            new_bal = await adjust_wallet(uid, delta)
        elif text.isdigit():
            new_bal = await set_wallet_balance(uid, int(text))
        else:
            await update.message.reply_text("فرمت نامعتبر")
            return True
        await update.message.reply_text(f"✅ موجودی {uid}: {new_bal:,} تومان")
        return True

    return False
