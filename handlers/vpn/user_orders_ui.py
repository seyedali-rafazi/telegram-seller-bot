# handlers/vpn/user_orders_ui.py — سفارش‌ها و کانفیگ‌ها (کاربر)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.messages import msg
from core.formatting import msg_e, h, format_sub_delivery
from core.keyboards import get_main_menu_keyboard
from core.database import get_user_info, get_bale_request
from handlers.vpn.referral import build_referral_section
from core.database.user_orders import (
    get_user_pending_orders_detailed,
    get_user_orders_history,
    get_user_subscriptions_all,
    get_subscription_by_id,
    count_user_orders_by_status,
)
from core.database.bale_requests import get_user_bale_requests, count_user_bale_by_status
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


async def _hub_counts(uid: str):
    order_counts = await count_user_orders_by_status(uid)
    bale_counts = await count_user_bale_by_status(uid)
    return {
        "pending": order_counts["pending"] + bale_counts["pending"],
        "approved": order_counts["approved"] + bale_counts["approved"],
        "rejected": order_counts["rejected"],
        "order_pending": order_counts["pending"],
        "bale_pending": bale_counts["pending"],
    }


async def _hub_text(uid: str) -> str:
    counts = await _hub_counts(uid)
    lines = [
        "📋 **سفارش‌ها و ساب**",
        "",
        f"⏳ در انتظار: **{counts['pending']}**",
        f"✅ تحویل‌شده: **{counts['approved']}**",
        f"❌ رد شده: **{counts['rejected']}**",
    ]
    if counts["bale_pending"]:
        lines.append(f"  _(شامل {counts['bale_pending']} درخواست بله)_")
    return "\n".join(lines)


async def btn_orders_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_chat.id)
    text = await _hub_text(uid)
    await update.message.reply_text(
        text + "\n\nگزینه را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=user_hub_keyboard(),
    )


async def user_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.message.chat_id)
    data = query.data

    if data == "usr_hub":
        text = await _hub_text(uid)
        await query.edit_message_text(
            text,
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
        referral_section = await build_referral_section(uid)
        text = msg("account_title") + "\n\n" + msg(
            "account_body",
            uid=h(uid),
            username=h(f"@{username}" if username else "—"),
            join_date=h(join_date or "—"),
            referral_section=referral_section,
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
        orders = await get_user_pending_orders_detailed(uid)
        bale_rows = await get_user_bale_requests(uid, status="pending")
        if not orders and not bale_rows:
            await query.edit_message_text(
                "⏳ سفارش در انتظاری ندارید.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")]]
                ),
            )
            return
        lines = ["⏳ **در انتظار ارسال ساب توسط ادمین:**\n"]
        for r in orders:
            lines.append(
                f"• `{r[1]}` — {r[2]} — {r[3]:,} تومان — {r[4][:10]}"
            )
        for r in bale_rows:
            _, code, bale_id, _, _, created, _ = r
            lines.append(f"• `{code}` — 🔗 بله — شناسه `{bale_id}` — {created[:10]}")
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")]]
            ),
        )
        return

    if data == "usr_configs":
        paid_rows = await get_user_subscriptions_all(uid)
        paid_live = [r for r in paid_rows if r[6] == 1]
        bale_rows = await get_user_bale_requests(uid, status="approved")
        bale_with_sub = [r for r in bale_rows if r[4]]
        if not paid_live and not bale_with_sub:
            await query.edit_message_text(
                "🔗 ساب فعالی ندارید.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")]]
                ),
            )
            return
        kb = []
        for s in paid_live:
            sub_id, code, pname, _, _, _, _ = s
            kb.append(
                [
                    InlineKeyboardButton(
                        f"💰 {code} — {pname}",
                        callback_data=f"usr_sub_{sub_id}",
                    )
                ]
            )
        for r in bale_with_sub:
            rid, code, bale_id, _, _, _, reviewed = r
            date = (reviewed or "")[:10] or "—"
            kb.append(
                [
                    InlineKeyboardButton(
                        f"🔗 {code} — بله {bale_id} — {date}",
                        callback_data=f"usr_bale_{rid}",
                    )
                ]
            )
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")])
        await query.edit_message_text(
            "🔗 **ساب‌های من** — برای مشاهده لینک کلیک کنید:\n"
            "💰 = خرید پولی | 🔗 = اشتراک بله",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    if data == "usr_history":
        order_rows = await get_user_orders_history(uid, limit=25)
        bale_rows = await get_user_bale_requests(uid, status="approved")
        if not order_rows and not bale_rows:
            await query.edit_message_text(
                "📜 تاریخچه‌ای وجود ندارد.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data="usr_hub")]]
                ),
            )
            return
        kb = []
        lines = ["📜 **تاریخچه:**\n"]
        for r in order_rows[:20]:
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
        for r in bale_rows:
            rid, code, bale_id, _, sub_url, created, reviewed = r
            if not sub_url:
                continue
            date = (reviewed or created or "")[:10] or "—"
            lines.append(f"• `{code}` — ✅ بله — شناسه `{bale_id}` — {date}")
            kb.append(
                [
                    InlineKeyboardButton(
                        f"👁 بله {code}",
                        callback_data=f"usr_bale_{rid}",
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

    if data.startswith("usr_bale_"):
        request_id = int(data.replace("usr_bale_", ""))
        req = await get_bale_request(request_id)
        if not req or str(req["user_id"]) != uid or req["status"] != "approved":
            await query.answer("یافت نشد", show_alert=True)
            return
        sub_url = req["sub_url"]
        if not sub_url:
            await query.answer("ساب موجود نیست", show_alert=True)
            return
        date = (req["reviewed_at"] or "")[:10] or "—"
        text = msg_e(
            "bale_sub_approved_user",
            bale_id=req["bale_id"],
            date=date,
            sub_body=format_sub_delivery(sub_url),
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
