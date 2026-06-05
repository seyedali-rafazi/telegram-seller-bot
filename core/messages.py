# core/messages.py — متن‌های فارسی ربات

MESSAGES = {
    "welcome": (
        "👋 به ربات VPN خوش آمدید!\n\n"
        "از منوی زیر گزینه مورد نظر را انتخاب کنید."
    ),
    "banned": "🚫 حساب شما مسدود شده است. با پشتیبانی تماس بگیرید.",
    "plans_title": "📦 پلن‌های موجود:\n\nروی پلن مورد نظر کلیک کنید:",
    "no_plans": "❌ در حال حاضر پلنی ثبت نشده است.",
    "plan_item": "{name}\n⏱ {days} روز | 📊 {gb} گیگ | 💰 {price:,} تومان",
    "confirm_buy": (
        "🛒 تأیید خرید\n\n"
        "پلن: {name}\n"
        "قیمت: {price:,} تومان\n"
        "موجودی کیف پول: {balance:,} تومان\n\n"
        "آیا خرید را تأیید می‌کنید؟"
    ),
    "insufficient_balance": (
        "❌ موجودی کیف پول کافی نیست.\n"
        "مورد نیاز: {price:,} تومان — موجودی: {balance:,} تومان\n\n"
        "از منو «شارژ کیف پول» استفاده کنید."
    ),
    "order_submitted": (
        "✅ سفارش شما ثبت شد.\n\n"
        "کد سفارش: <code>{order_code}</code>\n"
        "پلن: {name}\n"
        "مبلغ: {price:,} تومان (از کیف پول کسر شد)\n"
        "موجودی باقی‌مانده: <b>{new_balance:,}</b> تومان\n\n"
        "پس از بررسی ادمین، لینک اشتراک (Subscription) برای شما ارسال می‌شود."
    ),
    "too_many_pending": (
        "❌ شما {count} سفارش در انتظار دارید.\n"
        "لطفاً تا بررسی سفارش‌های قبلی صبر کنید."
    ),
    "order_pending_line": "⏳ {order_code} — {name} ({price:,} تومان)",
    "order_approved_user": (
        "✅ سفارش <code>{order_code}</code> تأیید شد.\n\n"
        "پلن: {name}\n"
        "اعتبار تا: {expires}\n\n"
        "{sub_body}"
    ),
    "sub_link_body": (
        "🔗 <b>لینک اشتراک (Subscription):</b>\n\n"
        "<code>{sub_url}</code>\n\n"
        "📱 <b>نحوه استفاده:</b>\n"
        "۱. لینک بالا را کپی کنید.\n"
        "۲. در v2rayNG / Hiddify / Streisand به‌عنوان Subscription اضافه کنید.\n"
        "۳. Update / بروزرسانی بزنید تا کانفیگ‌ها از ساب لود شوند."
    ),
    "order_rejected_user": (
        "❌ سفارش <code>{order_code}</code> رد شد.\n"
        "مبلغ {refund:,} تومان به کیف پول شما برگشت.\n"
        "در صورت نیاز با پشتیبانی تماس بگیرید."
    ),
    "account_title": "👤 <b>حساب کاربری</b>",
    "account_body": (
        "🆔 شناسه: <code>{uid}</code>\n"
        "👤 نام کاربری: {username}\n"
        "💰 موجودی کیف پول: <b>{balance:,}</b> تومان\n"
        "📅 عضویت از: {join_date}\n\n"
        "<b>سفارش‌های در انتظار:</b>\n{pending_orders}\n\n"
        "<b>سرویس‌های فعال:</b>\n{services}"
    ),
    "no_active_service": "— هیچ سرویس فعالی ندارید —",
    "no_pending_orders": "— سفارش در انتظاری ندارید —",
    "service_line": "• {name} — تا {expires}",
    "wallet_intro": (
        "💳 <b>شارژ کیف پول (کارت به کارت)</b>\n\n"
        "مبلغی که می‌خواهید شارژ کنید را به <b>تومان</b> ارسال کنید.\n"
        "مثال: <code>50000</code>"
    ),
    "wallet_pay_instructions": (
        "💳 مبلغ شارژ: <b>{amount:,}</b> تومان\n\n"
        "۱. این مبلغ را به کارت زیر واریز کنید:\n"
        "<code>{card}</code>\n"
        "به نام: {card_name}\n\n"
        "۲. سپس عکس رسید (فیش) واریز را ارسال کنید.\n\n"
        "پس از تأیید ادمین، موجودی شما شارژ می‌شود."
    ),
    "card_not_set": "⚠️ شماره کارت هنوز تنظیم نشده. با پشتیبانی تماس بگیرید.",
    "invalid_amount": "❌ مبلغ نامعتبر است. یک عدد صحیح بزرگ‌تر از صفر وارد کنید.",
    "upload_receipt": "📸 لطفاً عکس رسید واریز را ارسال کنید:",
    "receipt_submitted": (
        "✅ درخواست شارژ ثبت شد.\n"
        "کد پرداخت: <code>{payment_code}</code>\n"
        "مبلغ: {amount:,} تومان\n\n"
        "پس از بررسی ادمین، موجودی شما به‌روز می‌شود."
    ),
    "support_guide": (
        "📖 <b>راهنمای اتصال VPN</b>\n\n"
        "<b>اندروید (v2rayNG / Hiddify):</b>\n"
        "۱. لینک Subscription را از ربات کپی کنید.\n"
        "۲. در اپ: Subscription → + → Paste link\n"
        "۳. Update بزنید و یک کانفیگ را انتخاب کنید.\n\n"
        "<b>iOS (Streisand / V2Box):</b>\n"
        "۱. لینک Subscription را import کنید.\n"
        "۲. Subscription را بروزرسانی کنید.\n"
        "۳. اتصال را فعال کنید.\n\n"
        "برای سوالات بیشتر با ادمین تماس بگیرید."
    ),
    "contact_admin": "💬 تماس با ادمین",
    "channel_required": (
        "🛑 برای استفاده از ربات، ابتدا باید در کانال ما عضو شوید.\n"
        "پس از عضویت مجدداً /start را ارسال کنید."
    ),
    "join_channel_btn": "📢 عضویت در کانال",
    "bale_sub_ask_id": (
        "🔗 <b>اشتراک بله</b>\n\n"
        "اگر در ربات بله اشتراک Pro دارید، "
        "شناسه عددی خود را از بخش «حساب کاربری» در ربات بله پیدا کنید "
        "و در پیام بعدی برای ما ارسال کنید."
    ),
    "bale_sub_invalid_id": "❌ شناسه نامعتبر است. فقط عدد ارسال کنید.",
    "bale_sub_pending_wait": (
        "⏳ درخواست قبلی شما هنوز در انتظار بررسی است.\n\n"
        "لطفاً تا پاسخ به درخواست اول صبر کنید و دوباره شناسه ارسال نکنید."
    ),
    "bale_sub_received": (
        "✅ درخواست شما ثبت شد.\n\n"
        "پس از بررسی ادمین، لینک اشتراک در بخش «📋 سفارش‌ها و ساب» → «🔗 ساب‌های من» قرار می‌گیرد."
    ),
    "bale_sub_approved_user": (
        "✅ درخواست اشتراک بله تأیید شد.\n\n"
        "شناسه بله: <code>{bale_id}</code>\n"
        "تاریخ: {date}\n\n"
        "{sub_body}"
    ),
    "test_config_success": (
        "🧪 <b>ساب تست</b>\n\n"
        "یک‌بار برای هر کاربر\n\n"
        "{sub_body}"
    ),
    "test_config_already_used": (
        "ℹ️ شما قبلاً ساب تست دریافت کرده‌اید.\n\n"
        "{sub_body}"
    ),
    "test_config_empty": (
        "❌ در حال حاضر ساب تست موجود نیست.\n\n"
        "لطفاً چند ساعت دیگر دوباره تلاش کنید."
    ),
}


def msg(key: str, **kwargs) -> str:
    text = MESSAGES.get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
