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
        "پس از بررسی ادمین، لینک VPN برای شما ارسال می‌شود."
    ),
    "too_many_pending": (
        "❌ شما {count} سفارش در انتظار دارید.\n"
        "لطفاً تا بررسی سفارش‌های قبلی صبر کنید."
    ),
    "order_pending_line": "⏳ {order_code} — {name} ({price:,} تومان)",
    "order_approved_user": (
        "✅ سفارش <code>{order_code}</code> تأیید شد.\n\n"
        "کد اشتراک: <code>{sub_code}</code>\n"
        "پلن: {name}\n"
        "اعتبار تا: {expires}\n\n"
        "🔗 کانفیگ VPN:\n\n"
        "<code>{config}</code>"
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
        "۱. مبلغ را به شماره کارت زیر واریز کنید:\n"
        "<code>{card}</code>\n"
        "به نام: {card_name}\n\n"
        "۲. مبلغ واریزی (به تومان) را در پیام بعدی ارسال کنید.\n"
        "۳. سپس عکس رسید را آپلود کنید.\n\n"
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
        "<b>اندروید:</b>\n"
        "۱. اپ v2rayNG یا Hiddify را نصب کنید.\n"
        "۲. کانفیگ دریافتی را کپی کنید.\n"
        "۳. از منو Import from clipboard را بزنید.\n"
        "۴. اتصال را فعال کنید.\n\n"
        "<b>iOS:</b>\n"
        "۱. Streisand یا V2Box را از App Store نصب کنید.\n"
        "۲. لینک کانفیگ را import کنید.\n"
        "۳. Allow VPN Configuration را تأیید کنید.\n\n"
        "برای سوالات بیشتر با ادمین تماس بگیرید."
    ),
    "contact_admin": "💬 تماس با ادمین",
    "channel_required": (
        "🛑 برای استفاده از ربات، ابتدا باید در کانال ما عضو شوید.\n"
        "پس از عضویت مجدداً /start را ارسال کنید."
    ),
    "join_channel_btn": "📢 عضویت در کانال",
}


def msg(key: str, **kwargs) -> str:
    text = MESSAGES.get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
