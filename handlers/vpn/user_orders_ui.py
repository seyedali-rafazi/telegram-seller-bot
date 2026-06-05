# handlers/vpn/user_orders_ui.py — سفارش‌ها و کانفیگ‌ها (کاربر)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.messages import msg
from core.formatting import msg_e, h, format_sub_delivery
from core.keyboards import get_main_menu_keyboard
from core.database import get_wallet_balance, get_user_info
from core.database.user_orders import (
    get_user_pending_orders_detailed,
    get_user_orders_history,
    get_user_subscriptions_all,
    get_subscription_by_id,
    count_user_orders_by_status,
)
from core.database.orders import get_order


STATUS_FA = {
    "pending": "⏳ در انتظار ساب",
    "approved": "✅ تحویل شده",
    "rejected": "❌ رد شده",
}


def user_hub_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏳ سفارش‌های در انتظار", callback_data="usr_pending")],
            [InlineKeyboardButton("🔗 ساب‌های من", callback_data="usr_configs")],
            [InlineKeyboardButton("📜 تاریخچه سفارش‌ها", callback_data="usr_history")],
            [InlineKeyboardButton("👤 خلاصه حساب", callback_data="usr_summary")],
        ]
    )


async def btn_orders_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_chat.id)
    counts = await count_user_orders_by_status(uid)
    await update.message.reply_text(
        f"📋 **سفارش‌ها و ساب**\n\n"
        f"⏳ در انتظار: **{counts['pending']}**\n"
        f"✅ تحویل‌شده: **{counts['approved']}**\n"
        f"❌ رد شده: **{counts['rejected']}**\n\n"
        "گزینه را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=user_hub_keyboard(),
    )


async def user_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    data = query.data

    if data == "usr_hub":
        counts = await count_user_orders_by_status(uid)
        await query.edit_message_text(
            f"📋 **سفارش‌ها و ساب**\n\n"
            f"⏳ در انتظار: **{counts['pending']}**\n"
            f"✅ تحویل‌شده: **{counts['approved']}**\n"
            f"❌ رد شده: **{counts['rejected']}**",
            parse_mode="Markdown",
            reply_markup=user_hub_keyboard(),
        )
        return

    if data == "usr_summary":
        info = await get_user_info(uid)
        if not info:
            await query.edit_message_text("❌ /start را بزنید.")
            return
        username, _, join_date, _ = info
        balance = await get_wallet_balance(uid)
        pending = await get_user_pending_orders_detailed(uid)
        pending_txt = (
            "\n".join(
                msg_e("order_pending_line", order_code=p[1], name=p[2], price=p[3])
                for p in pending
            )
            if pending
            else msg("no_pending_orders")
        )
        subs_live = [s for s in await get_user_subscriptions_all(uid) if s[6] == 1]
        svc_txt = (
            "\n".join(
                msg_e("service_line", name=s[2], expires=s[3][:10]) for s in subs_live
            )
            if subs_live
            else msg("no_active_service")
        )
        text = msg("account_title") + "\n\n" + msg(
            "account_body",
            uid=h(uid),
            username=h(f"@{username}" if username else "—"),
            balance=balance,
            join_date=h(join_date or "—"),
            pending_orders=pending_txt,
            services=svc_txt,
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")]]
            ),
        )
        return

    if data == "usr_pending":
        rows = await get_user_pending_orders_detailed(uid)
        if not rows:
            await query.edit_message_text(
                "⏳ سفارش در انتظاری ندارید.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")]]
                ),
            )
            return
        lines = ["⏳ **در انتظار ارسال ساب توسط ادمین:**\n"]
        for r in rows:
            lines.append(
                f"• `{r[1]}` — {r[2]} — {r[3]:,} تومان — {r[4][:10]}"
            )
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")]]
            ),
        )
        return

    if data == "usr_configs":
        rows = await get_user_subscriptions_all(uid)
        live = [r for r in rows if r[6] == 1]
        if not live:
            await query.edit_message_text(
                "🔗 ساب فعالی ندارید.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")]]
                ),
            )
            return
        kb = []
        for s in live:
            sub_id, code, pname, expires, _, _, _ = s
            kb.append(
                [
                    InlineKeyboardButton(
                        f"🔗 {code} — {pname}",
                        callback_data=f"usr_sub_{sub_id}",
                    )
                ]
            )
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")])
        await query.edit_message_text(
            "🔗 **ساب‌های فعال** — برای مشاهده لینک کلیک کنید:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    if data == "usr_history":
        rows = await get_user_orders_history(uid, limit=25)
        if not rows:
            await query.edit_message_text(
                "📜 تاریخچه‌ای وجود ندارد.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")]]
                ),
            )
            return
        kb = []
        lines = ["📜 **تاریخچه سفارش‌ها:**\n"]
        for r in rows[:20]:
            oid, code, status, pname, amount, created, cfg, _ = r
            st = STATUS_FA.get(status, status)
            lines.append(f"• `{code}` — {st} — {pname}")
            if status == "approved" and cfg:
                kb.append(
                    [
                        InlineKeyboardButton(
                            f"👁 ساب {code}",
                            callback_data=f"usr_ord_{oid}",
                        )
                    ]
                )
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")])
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    if data.startswith("usr_sub_"):
        sub_id = int(data.replace("usr_sub_", ""))
        sub = await get_subscription_by_id(sub_id)
        if not sub or str(sub["user_id"]) != uid:
            await query.answer("یافت نشد", show_alert=True)
            return
        cfg = sub["config_text"] or "—"
        code = sub["public_id"] or f"SUB-{sub_id:08d}"
        text = msg_e(
            "order_approved_user",
            order_code=code,
            name=sub["plan_name"],
            expires=sub["expires_at"][:10],
            sub_body=format_sub_delivery(cfg),
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔙 ساب‌ها", callback_data="usr_configs")],
                    [InlineKeyboardButton("📋 منو", callback_data="usr_hub")],
                ]
            ),
        )
        return

    if data.startswith("usr_ord_"):
        order_id = int(data.replace("usr_ord_", ""))
        order = await get_order(order_id)
        if not order or str(order["user_id"]) != uid:
            await query.answer("یافت نشد", show_alert=True)
            return
        if order["status"] != "approved" or not order["config_text"]:
            await query.answer("ساب موجود نیست", show_alert=True)
            return
        from core.database.plans import get_plan

        plan = await get_plan(order["plan_id"])
        pname = plan[1] if plan else "—"
        text = msg_e(
            "order_approved_user",
            order_code=order["public_id"],
            name=pname,
            expires=(order["reviewed_at"] or "")[:10],
            sub_body=format_sub_delivery(order["config_text"]),
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔙 تاریخچه", callback_data="usr_history")],
                    [InlineKeyboardButton("📋 منو", callback_data="usr_hub")],
                ]
            ),
        )
        return
