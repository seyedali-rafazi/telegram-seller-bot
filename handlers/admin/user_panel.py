# handlers/admin/user_panel.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.config import is_admin_chat, get_primary_admin_id
from core.state_manager import set_state
from core.constants import STATE_ADMIN_ORDER_CONFIG
from core.database import get_wallet_balance, get_order
from core.database.users import get_user_info, is_user_banned
from core.database.user_orders import (
    get_user_pending_orders_detailed,
    get_user_orders_history,
    count_user_orders_by_status,
    get_user_subscriptions_all,
)
from core.formatting import h

PARSE = "HTML"


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
        return f"❌ کاربر <code>{h(user_id)}</code> در دیتابیس یافت نشد."

    username, _, join_date, _ = info
    uname = f"@{username}" if username else "—"
    balance = await get_wallet_balance(user_id)
    banned = await is_user_banned(user_id)
    counts = await count_user_orders_by_status(user_id)
    subs = await get_user_subscriptions_all(user_id)
    live_subs = sum(1 for s in subs if s[6] == 1)

    return (
        f"👤 <b>پروفایل کاربر</b>\n\n"
        f"🆔 شناسه: <code>{h(user_id)}</code>\n"
        f"👤 یوزرنیم: {h(uname)}\n"
        f"💰 موجودی: <b>{balance:,}</b> تومان\n"
        f"📅 عضویت: {h(join_date or '—')}\n"
        f"🚫 مسدود: {'بله' if banned else 'خیر'}\n\n"
        f"📦 سفارش‌ها:\n"
        f"  ⏳ در انتظار کانفیگ: <b>{counts['pending']}</b>\n"
        f"  ✅ انجام‌شده: <b>{counts['approved']}</b>\n"
        f"  ❌ رد شده: <b>{counts['rejected']}</b>\n\n"
        f"🔗 اشتراک فعال: <b>{live_subs}</b>"
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


def pending_orders_list_keyboard(rows, back_callback: str = "adm_back") -> InlineKeyboardMarkup:
    """rows: id, public_id, user_id, amount, created_at, plan_name"""
    kb = []
    for r in rows:
        oid, code, uid, amount, _, pname = r[0], r[1], r[2], r[3], r[4], r[5]
        label = f"📤 {code}"[:60]
        kb.append(
            [
                InlineKeyboardButton(label, callback_data=f"adm_fulfill_{oid}"),
                InlineKeyboardButton("❌", callback_data=f"order_no_{oid}"),
            ]
        )
        kb.append(
            [
                InlineKeyboardButton(
                    f"👤 {uid[-8:]} — {pname[:20]}",
                    callback_data=f"adm_uhome_{uid}",
                )
            ]
        )
    kb.append([InlineKeyboardButton("🔙 پنل ادمین", callback_data=back_callback)])
    return InlineKeyboardMarkup(kb)


async def send_user_panel(update: Update, user_id: str, *, edit_message=None):
    counts = await count_user_orders_by_status(user_id)
    text = await build_user_summary_text(user_id)
    kb = user_panel_keyboard(user_id, counts)

    if edit_message:
        await edit_message.edit_message_text(text, parse_mode=PARSE, reply_markup=kb)
    else:
        await update.message.reply_text(text, parse_mode=PARSE, reply_markup=kb)


async def cmd_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin_chat(update.effective_chat.id):
        return
    if not context.args:
        await update.message.reply_text(
            "❌ فرمت:\n<code>/user 123456789</code>\n\n"
            "شناسه عددی کاربر را از پیام یا پروفایل کپی کنید.",
            parse_mode=PARSE,
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
            oid, code, pname = r[0], r[1], r[2]
            kb.append(
                [
                    InlineKeyboardButton(
                        f"📤 {code} — {pname[:25]}",
                        callback_data=f"adm_fulfill_{oid}",
                    ),
                    InlineKeyboardButton("❌", callback_data=f"order_no_{oid}"),
                ]
            )
        kb.append(
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"adm_uhome_{user_id}")]
        )
        await query.edit_message_text(
            f"⏳ <b>سفارش‌های در انتظار</b> — <code>{h(user_id)}</code>\n\n"
            "روی 📤 بزنید → پیام بعدی لینک VPN را بفرستید:",
            parse_mode=PARSE,
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
        lines = [f"✅ <b>سفارش‌های موفق</b> — <code>{h(user_id)}</code>\n"]
        for r in rows[:15]:
            oid, code, pname, amount = r[0], r[1], r[3], r[4]
            lines.append(f"• <code>{h(code)}</code> — {h(pname)} — {amount:,}ت")
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
            parse_mode=PARSE,
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
                    [
                        [
                            InlineKeyboardButton(
                                "🔙 بازگشت", callback_data=f"adm_uhome_{user_id}"
                            )
                        ]
                    ]
                ),
            )
            return True
        lines = [f"❌ <b>رد شده</b> — <code>{h(user_id)}</code>\n"]
        for r in rows:
            lines.append(
                f"• <code>{h(r[1])}</code> — {h(r[3])} — {r[4]:,}ت — {r[5][:10]}"
            )
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode=PARSE,
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
            f"📤 <b>ارسال کانفیگ</b>\n\n"
            f"کد: <code>{h(code)}</code>\n"
            f"کاربر: <code>{h(order['user_id'])}</code>\n"
            f"مبلغ: {order['amount']:,} تومان\n\n"
            f"⏳ <b>لینک VPN را در پیام بعدی بفرستید.</b>",
            parse_mode=PARSE,
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
            f"📋 <b>جزئیات سفارش</b>\n\n"
            f"کد: <code>{h(code)}</code>\n"
            f"وضعیت: {st}\n"
            f"کاربر: <code>{h(uid)}</code>\n"
            f"پلن: {h(pname)}\n"
            f"مبلغ: {order['amount']:,} تومان\n"
            f"تاریخ: {h(order['created_at'][:16])}\n\n"
            f"🔗 <b>کانفیگ ارسال‌شده:</b>\n\n"
            f"<code>{h(cfg)}</code>"
        )
        await query.edit_message_text(
            text,
            parse_mode=PARSE,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 پروفایل کاربر", callback_data=f"adm_uhome_{uid}")]]
            ),
        )
        return True

    return False
