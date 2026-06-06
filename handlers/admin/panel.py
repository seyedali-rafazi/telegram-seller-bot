# handlers/admin/panel.py

import asyncio
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.config import is_admin_chat, get_primary_admin_id
from core.keyboards import get_admin_menu_keyboard
from core.state_manager import set_state, clear_state, get_state
from core.constants import (
    STATE_ADMIN_BROADCAST,
    STATE_ADMIN_CONFIGS,
    STATE_ADMIN_TEST_CONFIGS,
    STATE_ADMIN_PLAN_NAME,
    STATE_ADMIN_PLAN_DAYS,
    STATE_ADMIN_PLAN_GB,
    STATE_ADMIN_PLAN_PRICE,
    STATE_ADMIN_USER_BALANCE,
    STATE_ADMIN_ORDER_CONFIG,
    STATE_ADMIN_BALE_SUB,
    STATE_ADMIN_REFERRAL_CONFIGS,
)
from core.database import (
    get_total_users,
    count_pending_payments,
    count_pending_orders,
    get_pending_orders,
    get_pending_payments,
    get_order,
    reject_purchase_order,
    fulfill_purchase_order,
    get_all_plans,
    count_available_configs,
    count_total_configs,
    get_all_users,
    approve_payment,
    reject_payment,
    get_payment,
    add_configs_bulk,
    add_test_configs_bulk,
    count_available_test_configs,
    count_total_test_configs,
    list_test_config_pool,
    delete_test_pool_item,
    add_referral_configs_bulk,
    count_available_referral_configs,
    count_total_referral_configs,
    list_referral_config_pool,
    delete_referral_pool_item,
    get_bale_request,
    fulfill_bale_request,
    count_pending_bale_requests,
    get_pending_bale_requests,
    get_approved_history_by_bale_id,
    get_approved_history_by_user_id,
    has_prior_bale_approval,
    build_bale_admin_history_text,
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
from core.formatting import msg_e, format_sub_delivery
from core.messages import msg


def _admin_key() -> str:
    return get_primary_admin_id()


def is_admin(update: Update) -> bool:
    return is_admin_chat(update.effective_chat.id)


async def _begin_bale_sub_send(query, request_id: int, req) -> None:
    set_state(_admin_key(), STATE_ADMIN_BALE_SUB, request_id=request_id)
    code = req["public_id"] or f"BALE-{request_id:08d}"
    bale_history = await get_approved_history_by_bale_id(
        req["bale_id"], exclude_request_id=request_id
    )
    user_history = await get_approved_history_by_user_id(
        req["user_id"], exclude_request_id=request_id
    )
    history_text = build_bale_admin_history_text(
        bale_history,
        user_history,
        current_bale_id=req["bale_id"],
        current_user_id=req["user_id"],
    )
    await query.edit_message_text(
        f"📤 <b>ارسال ساب — اشتراک بله</b>\n\n"
        f"کد: <code>{code}</code>\n"
        f"کاربر: <code>{req['user_id']}</code>\n"
        f"شناسه بله: <code>{req['bale_id']}</code>\n\n"
        f"{history_text}\n\n"
        f"⏳ <b>لینک Subscription را در پیام بعدی بفرستید.</b>",
        parse_mode="HTML",
        reply_markup=None,
    )


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    pending_pay = await count_pending_payments()
    pending_ord = await count_pending_orders()
    avail = await count_available_configs()
    test_avail = await count_available_test_configs()
    ref_avail = await count_available_referral_configs()
    bale_pending = await count_pending_bale_requests()
    await update.message.reply_text(
        f"🛠 **پنل ادمین**\n\n"
        f"پرداخت‌های در انتظار: {pending_pay}\n"
        f"سفارش‌های در انتظار: {pending_ord}\n"
        f"درخواست بله: {bale_pending}\n"
        f"ساب پولی آزاد: {avail}\n"
        f"ساب تست آزاد: {test_avail}\n"
        f"ساب دعوت آزاد: {ref_avail}\n\n"
        "گزینه را انتخاب کنید.\n\nراهنما: /help",
        parse_mode="Markdown",
        reply_markup=get_admin_menu_keyboard(),
    )


async def _show_test_pool_list(query) -> None:
    rows = await list_test_config_pool(25)
    avail = await count_available_test_configs()
    total = await count_total_test_configs()
    kb = []
    lines = [
        f"🧪 **مدیریت ساب تست**",
        f"آزاد: **{avail}** / کل: **{total}**",
        "",
        "روی 🗑 بزنید تا حذف شود.",
        "اگر به کاربری داده شده باشد، دسترسی تست او هم پاک می‌شود.",
        "",
    ]
    if not rows:
        lines.append("لیست خالی است.")
    else:
        for r in rows:
            pid, url, is_assigned, assigned_to, created = (
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
            )
            preview = url if len(url) <= 48 else url[:45] + "…"
            if is_assigned and assigned_to:
                status = f"👤 `{assigned_to}`"
            else:
                status = "✅ آزاد"
            date = (created or "")[:10] or "—"
            lines.append(f"**#{pid}** — {status} — {date}\n`{preview}`")
            kb.append(
                [
                    InlineKeyboardButton(
                        f"🗑 حذف #{pid}",
                        callback_data=f"adm_test_del_{pid}",
                    )
                ]
            )
    kb.append([InlineKeyboardButton("🔙 ساب تست", callback_data="adm_test_configs")])
    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def _show_referral_pool_list(query) -> None:
    rows = await list_referral_config_pool(25)
    avail = await count_available_referral_configs()
    total = await count_total_referral_configs()
    kb = []
    lines = [
        f"🎁 **مدیریت ساب دعوت**",
        f"آزاد: **{avail}** / کل: **{total}**",
        "",
        "روی 🗑 بزنید تا حذف شود.",
        "",
    ]
    if not rows:
        lines.append("لیست خالی است.")
    else:
        for r in rows:
            pid, url, is_assigned, assigned_to, created = (
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
            )
            preview = url if len(url) <= 48 else url[:45] + "…"
            if is_assigned and assigned_to:
                status = f"👤 `{assigned_to}`"
            else:
                status = "✅ آزاد"
            date = (created or "")[:10] or "—"
            lines.append(f"**#{pid}** — {status} — {date}\n`{preview}`")
            kb.append(
                [
                    InlineKeyboardButton(
                        f"🗑 حذف #{pid}",
                        callback_data=f"adm_ref_del_{pid}",
                    )
                ]
            )
    kb.append([InlineKeyboardButton("🔙 ساب دعوت", callback_data="adm_referral_configs")])
    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin_chat(query.message.chat_id):
        await query.answer()
        return

    from .user_panel import admin_user_panel_callback

    if await admin_user_panel_callback(update, context):
        return

    await query.answer()
    data = query.data

    if data == "adm_stats":
        total = await get_total_users()
        pending_pay = await count_pending_payments()
        pending_ord = await count_pending_orders()
        avail = await count_available_configs()
        total_cfg = await count_total_configs()
        test_avail = await count_available_test_configs()
        test_total = await count_total_test_configs()
        ref_avail = await count_available_referral_configs()
        ref_total = await count_total_referral_configs()
        bale_pending = await count_pending_bale_requests()
        await query.edit_message_text(
            f"📊 آمار\n\n"
            f"کاربران: {total}\n"
            f"پرداخت معلق: {pending_pay}\n"
            f"سفارش معلق: {pending_ord}\n"
            f"درخواست بله: {bale_pending}\n"
            f"ساب پولی: {avail} آزاد / {total_cfg} کل\n"
            f"ساب تست: {test_avail} آزاد / {test_total} کل\n"
            f"ساب دعوت: {ref_avail} آزاد / {ref_total} کل"
        )
        return

    if data == "adm_orders":
        from .user_panel import pending_orders_list_keyboard
        from core.formatting import h

        rows = await get_pending_orders(15)
        if not rows:
            await query.edit_message_text(
                "✅ سفارش معلقی نیست.",
                reply_markup=get_admin_menu_keyboard(),
            )
            return
        lines = [
            "🛒 <b>سفارش‌های در انتظار</b>\n\n"
            "📤 = ارسال ساب (پیام بعدی لینک Subscription)\n"
            "❌ = رد سفارش | 👤 = پروفایل کاربر\n"
        ]
        for r in rows:
            lines.append(
                f"\n<code>{h(r[1])}</code>\n"
                f"کاربر <code>{h(r[2])}</code> — {r[3]:,}ت — {h(r[5])}"
            )
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=pending_orders_list_keyboard(rows, back_callback="adm_back"),
        )
        return

    if data == "adm_payments":
        rows = await get_pending_payments(15)
        if not rows:
            await query.edit_message_text("✅ پرداخت معلقی نیست.")
            return
        lines = ["💳 **پرداخت‌های در انتظار:**\n"]
        for r in rows:
            lines.append(f"`{r[1]}` — کاربر `{r[2]}` — {r[3]:,} تومان")
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
        set_state(_admin_key(), STATE_ADMIN_PLAN_NAME)
        await query.edit_message_text("نام پلن را ارسال کنید (مثال: یک ماهه ۳۰ گیگ):")
        return

    if data.startswith("adm_delplan_"):
        pid = int(data.replace("adm_delplan_", ""))
        await delete_plan(pid)
        await query.edit_message_text(f"✅ پلن #{pid} حذف شد.")
        return

    if data == "adm_configs":
        set_state(_admin_key(), STATE_ADMIN_CONFIGS)
        avail = await count_available_configs()
        await query.edit_message_text(
            f"🔗 ساب آزاد (پولی): {avail}\n\n"
            "هر خط یک لینک Subscription:\n"
            "مثال: `https://panel.example.com/sub/abc123`\n"
            "یا فایل .txt آپلود کنید."
        )
        return

    if data == "adm_bale_requests":
        rows = await get_pending_bale_requests(15)
        if not rows:
            await query.edit_message_text(
                "✅ درخواست بله معلقی نیست.",
                reply_markup=get_admin_menu_keyboard(),
            )
            return
        lines = ["🔗 **درخواست‌های اشتراک بله:**\n"]
        kb = []
        for r in rows:
            rid, code, uid, bale_id, created = r[0], r[1], r[2], r[3], r[4]
            lines.append(
                f"• `{code}` — بله `{bale_id}` — کاربر `{uid}` — {created[:10]}"
            )
            kb.append(
                [
                    InlineKeyboardButton(
                        f"📤 {code}",
                        callback_data=f"adm_bale_send_{rid}",
                    ),
                    InlineKeyboardButton(
                        "👤",
                        callback_data=f"adm_uhome_{uid}",
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

    if data.startswith("adm_bale_send_"):
        request_id = int(data.replace("adm_bale_send_", ""))
        req = await get_bale_request(request_id)
        if not req or req["status"] != "pending":
            await query.answer("درخواست یافت نشد یا قبلاً بررسی شده", show_alert=True)
            return
        bale_history = await get_approved_history_by_bale_id(
            req["bale_id"], exclude_request_id=request_id
        )
        user_history = await get_approved_history_by_user_id(
            req["user_id"], exclude_request_id=request_id
        )
        if has_prior_bale_approval(bale_history, user_history, request_id):
            code = req["public_id"] or f"BALE-{request_id:08d}"
            history_text = build_bale_admin_history_text(
                bale_history,
                user_history,
                current_bale_id=req["bale_id"],
                current_user_id=req["user_id"],
            )
            await query.edit_message_text(
                f"⚠️ <b>ارسال مجدد ساب؟</b>\n\n"
                f"کد: <code>{code}</code>\n"
                f"کاربر: <code>{req['user_id']}</code>\n"
                f"شناسه بله: <code>{req['bale_id']}</code>\n\n"
                f"{history_text}\n\n"
                f"آیا مطمئن هستید می‌خواهید دوباره ساب ارسال کنید؟",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✅ بله، ارسال مجدد",
                                callback_data=f"adm_bale_resend_ok_{request_id}",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "❌ خیر، لغو",
                                callback_data=f"adm_bale_resend_no_{request_id}",
                            )
                        ],
                    ]
                ),
            )
            return
        await _begin_bale_sub_send(query, request_id, req)
        return

    if data.startswith("adm_bale_resend_ok_"):
        request_id = int(data.replace("adm_bale_resend_ok_", ""))
        req = await get_bale_request(request_id)
        if not req or req["status"] != "pending":
            await query.answer("درخواست یافت نشد یا قبلاً بررسی شده", show_alert=True)
            return
        await _begin_bale_sub_send(query, request_id, req)
        return

    if data.startswith("adm_bale_resend_no_"):
        request_id = int(data.replace("adm_bale_resend_no_", ""))
        req = await get_bale_request(request_id)
        code = (req["public_id"] if req else None) or f"BALE-{request_id:08d}"
        await query.edit_message_text(
            f"❌ ارسال ساب برای <code>{code}</code> لغو شد.\n"
            f"از /admin → 🔗 اشتراک بله می‌توانید دوباره اقدام کنید.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 پنل", callback_data="adm_back")]]
            ),
        )
        return

    if data == "adm_test_configs":
        avail = await count_available_test_configs()
        total = await count_total_test_configs()
        await query.edit_message_text(
            f"🧪 **ساب تست**\n\n"
            f"آزاد: **{avail}** / کل: **{total}**",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("➕ افزودن", callback_data="adm_test_add")],
                    [
                        InlineKeyboardButton(
                            "📋 مشاهده و حذف", callback_data="adm_test_list"
                        )
                    ],
                    [InlineKeyboardButton("🔙 پنل", callback_data="adm_back")],
                ]
            ),
        )
        return

    if data == "adm_test_add":
        set_state(_admin_key(), STATE_ADMIN_TEST_CONFIGS)
        avail = await count_available_test_configs()
        total = await count_total_test_configs()
        await query.edit_message_text(
            f"🧪 **افزودن ساب تست**\n\n"
            f"آزاد: **{avail}** / کل: **{total}**\n\n"
            "هر خط یک لینک اشتراک تست (sub URL):\n"
            "مثال:\n"
            "`https://panel.example.com/sub/abc123`\n\n"
            "متن یا فایل `.txt` بفرستید.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 ساب تست", callback_data="adm_test_configs")]]
            ),
        )
        return

    if data == "adm_test_list":
        await _show_test_pool_list(query)
        return

    if data.startswith("adm_test_del_"):
        pool_id = int(data.replace("adm_test_del_", ""))
        ok, reason = await delete_test_pool_item(pool_id)
        if not ok:
            await query.answer("یافت نشد", show_alert=True)
            return
        await query.answer("✅ حذف شد")
        await _show_test_pool_list(query)
        return

    if data == "adm_referral_configs":
        avail = await count_available_referral_configs()
        total = await count_total_referral_configs()
        await query.edit_message_text(
            f"🎁 **ساب دعوت (۱ گیگ)**\n\n"
            f"آزاد: **{avail}** / کل: **{total}**",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("➕ افزودن", callback_data="adm_ref_add")],
                    [
                        InlineKeyboardButton(
                            "📋 مشاهده و حذف", callback_data="adm_ref_list"
                        )
                    ],
                    [InlineKeyboardButton("🔙 پنل", callback_data="adm_back")],
                ]
            ),
        )
        return

    if data == "adm_ref_add":
        set_state(_admin_key(), STATE_ADMIN_REFERRAL_CONFIGS)
        avail = await count_available_referral_configs()
        total = await count_total_referral_configs()
        await query.edit_message_text(
            f"🎁 **افزودن ساب دعوت**\n\n"
            f"آزاد: **{avail}** / کل: **{total}**\n\n"
            "هر خط یک لینک Subscription (۱ گیگ روی پنل):\n"
            "مثال:\n"
            "`https://panel.example.com/sub/referral123`\n\n"
            "متن یا فایل `.txt` بفرستید.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 ساب دعوت", callback_data="adm_referral_configs")]]
            ),
        )
        return

    if data == "adm_ref_list":
        await _show_referral_pool_list(query)
        return

    if data.startswith("adm_ref_del_"):
        pool_id = int(data.replace("adm_ref_del_", ""))
        ok, reason = await delete_referral_pool_item(pool_id)
        if not ok:
            await query.answer("یافت نشد", show_alert=True)
            return
        await query.answer("✅ حذف شد")
        await _show_referral_pool_list(query)
        return

    if data == "adm_broadcast":
        set_state(_admin_key(), STATE_ADMIN_BROADCAST)
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
                        f"👤 {r[0][-6:]}",
                        callback_data=f"adm_uhome_{r[0]}",
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
        clear_state(_admin_key())
        pending_pay = await count_pending_payments()
        pending_ord = await count_pending_orders()
        avail = await count_available_configs()
        await query.edit_message_text(
            f"🛠 پنل ادمین\nپرداخت: {pending_pay} | سفارش: {pending_ord} | کانفیگ: {avail}",
            reply_markup=get_admin_menu_keyboard(),
        )
        return

    if data.startswith("order_ok_"):
        order_id = int(data.replace("order_ok_", ""))
        order = await get_order(order_id)
        if not order or order["status"] != "pending":
            await query.answer("سفارش یافت نشد یا قبلاً بررسی شده", show_alert=True)
            return
        set_state(_admin_key(), STATE_ADMIN_ORDER_CONFIG, order_id=order_id)
        order_code = order["public_id"] or f"ORD-{order_id:08d}"
        base = query.message.text or query.message.caption or ""
        from core.formatting import h

        await query.edit_message_text(
            (query.message.text or query.message.caption or "")
            + f"\n\n⏳ لینک Subscription برای <code>{h(order_code)}</code> را در <b>پیام بعدی</b> ارسال کنید.",
            parse_mode="HTML",
            reply_markup=None,
        )
        return

    if data.startswith("order_no_"):
        order_id = int(data.replace("order_no_", ""))
        order = await get_order(order_id)
        ok = await reject_purchase_order(order_id)
        if ok and order:
            base = query.message.text or ""
            await query.edit_message_text(
                base + "\n\n❌ سفارش رد شد.",
                reply_markup=None,
            )
            order_code = order["public_id"] or f"ORD-{order_id:08d}"
            try:
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=msg(
                        "order_rejected_user",
                        order_code=order_code,
                        refund=int(order["amount"]),
                    ),
                    parse_mode="HTML",
                )
            except Exception:
                pass
        else:
            await query.answer("خطا یا قبلاً بررسی شده", show_alert=True)
        return

    if data.startswith("adm_wallet_"):
        uid = data.replace("adm_wallet_", "")
        set_state(_admin_key(), STATE_ADMIN_USER_BALANCE, target_user=uid)
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
        payment = await get_payment(pid)
        ok, result = await approve_payment(pid)
        if ok and payment:
            pay_code = payment["public_id"] or f"PAY-{pid:08d}"
            cap = (query.message.caption or "") + f"\n\n✅ {pay_code} تأیید شد."
            await query.edit_message_caption(caption=cap, reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=result,
                    text=f"✅ پرداخت {pay_code} تأیید شد. کیف پول شما شارژ شد.",
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
            pay_code = payment["public_id"] or f"PAY-{pid:08d}"
            cap = (query.message.caption or "") + f"\n\n❌ {pay_code} رد شد."
            await query.edit_message_caption(caption=cap, reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=payment["user_id"],
                    text=f"❌ پرداخت {pay_code} رد شد. با پشتیبانی تماس بگیرید.",
                )
            except Exception:
                pass
        return


async def process_admin_state(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    if not is_admin_chat(update.effective_chat.id):
        return False

    state = get_state(_admin_key())
    step = state.get("step")
    if not step:
        return False

    text = (update.message.text or "").strip()

    if step == STATE_ADMIN_BROADCAST:
        clear_state(_admin_key())
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
        clear_state(_admin_key())
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
            f"✅ {added} ساب اضافه شد.\nساب آزاد: {avail}"
        )
        return True

    if step == STATE_ADMIN_TEST_CONFIGS:
        clear_state(_admin_key())
        if update.message.document:
            doc = await update.message.document.get_file()
            content = (await doc.download_as_bytearray()).decode(
                "utf-8", errors="ignore"
            )
            lines = content.splitlines()
        else:
            lines = text.splitlines()
        added = await add_test_configs_bulk(lines)
        avail = await count_available_test_configs()
        total = await count_total_test_configs()
        await update.message.reply_text(
            f"✅ {added} کانفیگ تست اضافه شد.\n"
            f"آزاد: {avail} / کل: {total}\n\n"
            f"برای حذف: /admin → 🧪 ساب تست → 📋 مشاهده و حذف"
        )
        return True

    if step == STATE_ADMIN_REFERRAL_CONFIGS:
        clear_state(_admin_key())
        if update.message.document:
            doc = await update.message.document.get_file()
            content = (await doc.download_as_bytearray()).decode(
                "utf-8", errors="ignore"
            )
            lines = content.splitlines()
        else:
            lines = text.splitlines()
        added = await add_referral_configs_bulk(lines)
        avail = await count_available_referral_configs()
        total = await count_total_referral_configs()
        await update.message.reply_text(
            f"✅ {added} ساب دعوت اضافه شد.\n"
            f"آزاد: {avail} / کل: {total}\n\n"
            f"برای حذف: /admin → 🎁 ساب دعوت → 📋 مشاهده و حذف"
        )
        return True

    if step == STATE_ADMIN_PLAN_NAME:
        set_state(_admin_key(), STATE_ADMIN_PLAN_DAYS, plan_name=text)
        await update.message.reply_text("تعداد روز (عدد):")
        return True

    if step == STATE_ADMIN_PLAN_DAYS:
        if not text.isdigit():
            await update.message.reply_text("عدد وارد کنید:")
            return True
        set_state(_admin_key(), STATE_ADMIN_PLAN_GB, plan_name=state["plan_name"], days=int(text))
        await update.message.reply_text("حجم GB (عدد):")
        return True

    if step == STATE_ADMIN_PLAN_GB:
        if not text.isdigit():
            await update.message.reply_text("عدد وارد کنید:")
            return True
        set_state(
            _admin_key(),
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
        clear_state(_admin_key())
        pid = await create_plan(
            state["plan_name"], state["days"], state["data_gb"], int(text)
        )
        await update.message.reply_text(f"✅ پلن #{pid} ایجاد شد.")
        return True

    if step == STATE_ADMIN_ORDER_CONFIG:
        order_id = state.get("order_id")
        clear_state(_admin_key())
        ok, reason, extra = await fulfill_purchase_order(order_id, text)
        if not ok:
            if reason == "invalid_config":
                await update.message.reply_text(
                    "❌ لینک Subscription نامعتبر است (حداقل ۱۰ کاراکتر)."
                )
            else:
                await update.message.reply_text(f"❌ خطا: {reason}")
            return True

        user_id = extra["user_id"]
        sub_body = format_sub_delivery(extra["config"])
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=msg_e(
                    "order_approved_user",
                    order_code=extra["order_public_id"],
                    name=extra["name"],
                    expires=extra["expires"],
                    sub_body=sub_body,
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass
        await update.message.reply_text(
            f"✅ سفارش {extra['order_public_id']} تکمیل شد.\n"
            f"ساب برای کاربر {user_id} ارسال شد."
        )
        return True

    if step == STATE_ADMIN_BALE_SUB:
        request_id = state.get("request_id")
        clear_state(_admin_key())
        ok, reason, extra = await fulfill_bale_request(request_id, text)
        if not ok:
            if reason == "invalid_sub":
                await update.message.reply_text(
                    "❌ لینک Subscription نامعتبر است (حداقل ۱۰ کاراکتر)."
                )
            else:
                await update.message.reply_text(f"❌ خطا: {reason}")
            return True

        user_id = extra["user_id"]
        sub_body = format_sub_delivery(extra["sub_url"])
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=msg_e(
                    "bale_sub_approved_user",
                    bale_id=extra["bale_id"],
                    date=(extra.get("reviewed_at") or "")[:10] or "—",
                    sub_body=sub_body,
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass
        await update.message.reply_text(
            f"✅ {extra['public_id']} — ساب برای کاربر {user_id} ارسال شد."
        )
        return True

    if step == STATE_ADMIN_USER_BALANCE:
        uid = state.get("target_user")
        clear_state(_admin_key())
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
