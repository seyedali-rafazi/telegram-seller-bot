# handlers/admin/user_panel.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.config import is_admin_chat, get_primary_admin_id
from core.state_manager import set_state
from core.constants import STATE_ADMIN_ORDER_CONFIG, STATE_ADMIN_USER_BALANCE
from core.database import get_wallet_balance, get_order
from core.database.users import get_user_info, is_user_banned
from core.database.user_orders import (
    get_user_pending_orders_detailed,
    get_user_orders_history,
    count_user_orders_by_status,
    get_user_subscriptions_all,
)
from core.formatting import h


def _admin_key() -> str:
    return get_primary_admin_id()


STATUS_FA = {
    "pending": "⏳ در انتظار",
    "approved": "✅ انجام‌شده",
    "rejected": "❌ رد شده",
}


async def build_user_summary_text(user_id: str) -> str:
    info = await get_user_info(user_id)
    if not info:
        return f"❌ کاربر `{user_id}` در دیتابیس یافت نشد."

    username, _, join_date, _ = info
    balance = await get_wallet_balance(user_id)
    banned = await is_user_banned(user_id)
    counts = await count_user_orders_by_status(user_id)
    subs = await get_user_subscriptions_all(user_id)
    live_subs = sum(1 for s in subs if s[6] == 1)

    return (
        f"👤 **پروفایل کاربر**\n\n"
        f"🆔 شناسه: `{user_id}`\n"
        f"👤 یوزرنیم: @{username or '—'}\n"
        f"💰 موجودی: **{balance:,}** تومان\n"
        f"📅 عضویت: {join_date or '—'}\n"
        f"🚫 مسدود: {'بله' if banned else 'خیر'}\n\n"
        f"📦 سفارش‌ها:\n"
        f"  ⏳ در انتظار کانفیگ: **{counts['pending']}**\n"
        f"  ✅ انجام‌شده: **{counts['approved']}**\n"
        f"  ❌ رد شده: **{counts['rejected']}**\n\n"
        f"🔗 اشتراک فعال: **{live_subs}**"
    )


def user_panel_keyboard(user_id: str, counts: dict) -> InlineKeyboardMarkup:
    pending_n = counts.get("pending", 0)
    done_n = counts.get("approved", 0)
    rej_n = counts.get("rejected", 0)
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"⏳ ارسال کانفیگ ({pending_n})",
                    callback_data=f"adm_upend_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    f"✅ سفارش‌های موفق ({done_n})",
                    callback_data=f"adm_udone_{user_id}",
                ),
                InlineKeyboardButton(
                    f"❌ رد شده ({rej_n})",
                    callback_data=f"adm_urej_{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "💰 تغییر موجودی",
                    callback_data=f"adm_wallet_{user_id}",
                ),
                InlineKeyboardButton(
                    "🔙 پروفایل",
                    callback_data=f"adm_uhome_{user_id}",
                ),
            ],
        ]
    )


async def send_user_panel(update: Update, user_id: str, *, edit_message=None):
    counts = await count_user_orders_by_status(user_id)
    text = await build_user_summary_text(user_id)
    kb = user_panel_keyboard(user_id, counts)

    if edit_message:
        await edit_message.edit_message_text(
            text, parse_mode="Markdown", reply_markup=kb
        )
    else:
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=kb
        )


async def cmd_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin_chat(update.effective_chat.id):
        return
    if not context.args:
        await update.message.reply_text(
            "❌ فرمت:\n`/user 123456789`\n\n"
            "شناسه عددی کاربر را از پیام یا پروفایل کپی کنید.",
            parse_mode="Markdown",
        )
        return
    user_id = context.args[0].strip()
    await send_user_panel(update, user_id)


async def admin_user_panel_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """Returns True if callback was handled."""
    query = update.callback_query
    if not is_admin_chat(query.message.chat_id):
        return False

    data = query.data
    if not (
        data.startswith("adm_uhome_")
        or data.startswith("adm_upend_")
        or data.startswith("adm_udone_")
        or data.startswith("adm_urej_")
        or data.startswith("adm_fulfill_")
        or data.startswith("adm_vord_")
    ):
        return False

    await query.answer()

    if data.startswith("adm_uhome_"):
        user_id = data.replace("adm_uhome_", "")
        await send_user_panel(update, user_id, edit_message=query)
        return True

    if data.startswith("adm_upend_"):
        user_id = data.replace("adm_upend_", "")
        rows = await get_user_pending_orders_detailed(user_id)
        if not rows:
            await query.edit_message_text(
                "⏳ سفارش در انتظاری برای این کاربر نیست.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_uhome_{user_id}")]]
                ),
            )
            return True
        kb = []
        for r in rows:
            oid, code, pname, amount, _ = r[0], r[1], r[2], r[3], r[4]
            kb.append(
                [
                    InlineKeyboardButton(
                        f"📤 {code} — {pname}",
                        callback_data=f"adm_fulfill_{oid}",
                    )
                ]
            )
        kb.append(
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_uhome_{user_id}")]
        )
        await query.edit_message_text(
            f"⏳ **سفارش‌های در انتظار** — کاربر `{user_id}`\n\n"
            "روی سفارش بزنید، سپس در پیام بعدی لینک VPN را ارسال کنید:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return True

    if data.startswith("adm_udone_"):
        user_id = data.replace("adm_udone_", "")
        rows = await get_user_orders_history(user_id, status="approved", limit=20)
        if not rows:
            await query.edit_message_text(
                "✅ سفارش موفقی ثبت نشده.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_uhome_{user_id}")]]
                ),
            )
            return True
        kb = []
        lines = [f"✅ **سفارش‌های موفق** — `{user_id}`\n"]
        for r in rows[:15]:
            oid, code, _, pname, amount, created, _, reviewed = (
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]
            )
            lines.append(f"• `{code}` — {pname} — {amount:,}ت")
            kb.append(
                [
                    InlineKeyboardButton(
                        f"👁 {code}",
                        callback_data=f"adm_vord_{oid}",
                    )
                ]
            )
        kb.append(
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_uhome_{user_id}")]
        )
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return True

    if data.startswith("adm_urej_"):
        user_id = data.replace("adm_urej_", "")
        rows = await get_user_orders_history(user_id, status="rejected", limit=20)
        if not rows:
            await query.edit_message_text(
                "❌ سفارش رد شده‌ای نیست.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_uhome_{user_id}")]]
                ),
            )
            return True
        lines = [f"❌ **رد شده** — `{user_id}`\n"]
        for r in rows:
            lines.append(f"• `{r[1]}` — {r[3]} — {r[4]:,}ت — {r[5][:10]}")
        lines.append("\n🔙 برای بازگشت دکمه زیر را بزنید.")
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_uhome_{user_id}")]]
            ),
        )
        return True

    if data.startswith("adm_fulfill_"):
        order_id = int(data.replace("adm_fulfill_", ""))
        order = await get_order(order_id)
        if not order or order["status"] != "pending":
            await query.answer("سفارش معتبر نیست", show_alert=True)
            return True
        set_state(_admin_key(), STATE_ADMIN_ORDER_CONFIG, order_id=order_id)
        code = order["public_id"]
        await query.edit_message_text(
            f"📤 **ارسال کانفیگ**\n\n"
            f"کد: `{code}`\n"
            f"کاربر: `{order['user_id']}`\n"
            f"مبلغ: {order['amount']:,} تومان\n\n"
            f"⏳ **لینک VPN را در پیام بعدی بفرستید.**",
            parse_mode="Markdown",
            reply_markup=None,
        )
        return True

    if data.startswith("adm_vord_"):
        order_id = int(data.replace("adm_vord_", ""))
        order = await get_order(order_id)
        if not order:
            await query.answer("یافت نشد", show_alert=True)
            return True
        from core.database.plans import get_plan

        plan = await get_plan(order["plan_id"])
        pname = plan[1] if plan else "—"
        code = order["public_id"]
        st = STATUS_FA.get(order["status"], order["status"])
        cfg = order["config_text"] or "—"
        if len(cfg) > 3500:
            cfg = cfg[:3500] + "…"
        uid = order["user_id"]
        text = (
            f"📋 **جزئیات سفارش**\n\n"
            f"کد: `{code}`\n"
            f"وضعیت: {st}\n"
            f"کاربر: `{uid}`\n"
            f"پلن: {pname}\n"
            f"مبلغ: {order['amount']:,} تومان\n"
            f"تاریخ: {order['created_at'][:16]}\n\n"
            f"🔗 **کانفیگ ارسال‌شده:**\n\n"
            f"<code>{h(cfg)}</code>"
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 پروفایل کاربر", callback_data=f"adm_uhome_{uid}")]]
            ),
        )
        return True

    return False
