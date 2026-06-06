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
        "قیمت: {price:,} تومان\n\n"
        "آیا خرید را تأیید می‌کنید؟"
    ),
    "buy_pay_instructions": (
        "💳 مبلغ پرداخت: <b>{price:,}</b> تومان\n"
        "پلن: {name}\n\n"
        "۱. این مبلغ را به کارت زیر واریز کنید:\n"
        "<code>{card}</code>\n"
        "به نام: {card_name}\n\n"
        "۲. سپس عکس رسید (فیش) واریز را ارسال کنید.\n\n"
        "پس از بررسی ادمین، لینک اشتراک برای شما ارسال می‌شود."
    ),
    "order_submitted": (
        "✅ سفارش شما ثبت شد.\n\n"
        "کد سفارش: <code>{order_code}</code>\n"
        "پلن: {name}\n"
        "مبلغ: {price:,} تومان\n\n"
        "پس از بررسی پرداخت توسط ادمین، لینک اشتراک (Subscription) برای شما ارسال می‌شود."
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
        "در صورت نیاز با پشتیبانی تماس بگیرید."
    ),
    "account_title": "👤 <b>حساب کاربری</b>",
    "account_body": (
        "🆔 شناسه: <code>{uid}</code>\n"
        "👤 نام کاربری: {username}\n"
        "📅 عضویت از: {join_date}\n\n"
        "<b>اینترنت رایگان از دعوت:</b>\n{referral_section}\n\n"
        "<b>سفارش‌های در انتظار:</b>\n{pending_orders}\n\n"
        "<b>سرویس‌های فعال:</b>\n{services}"
    ),
    "referral_section": (
        "<b>از لینک دعوت:</b>\n"
        "👥 دعوت موفق: <b>{invite_count}</b> نفر\n"
        "💾 موجود: <b>{link_available}</b> از <b>{link_earned}</b>\n\n"
        "<b>از کد دعوت خرید:</b>\n"
        "🎫 خرید با کد شما: <b>{code_use_count}</b> بار\n"
        "💾 موجود: <b>{code_available}</b> از <b>{code_earned}</b>\n"
        "🔑 کد اختصاصی: <code>{invite_code}</code>"
    ),
    "referral_menu": (
        "🎁 <b>دعوت دوستان</b>\n\n"
        "<b>لینک دعوت:</b> هر عضو جدید با لینک شما → "
        "<b>{reward_mb} مگابایت</b> (حداقل {claim_mb} مگ برای درخواست)\n\n"
        "<b>کد دعوت:</b> هر خرید <b>اول</b> با کد شما → "
        "<b>{promo_reward_mb} مگابایت</b> (۵ گیگ) — فقط یک‌بار برای هر نفر\n"
        "کد شما: <code>{invite_code}</code>\n\n"
        "با دکمه‌های زیر موجودی را یک‌جا برای ادمین ارسال کنید.\n\n"
        "{stats_block}"
    ),
    "referral_stats_block": (
        "🔗 لینک — موجود: <b>{link_available}</b> | "
        "🎫 کد — موجود: <b>{code_available}</b>"
    ),
    "referral_link": (
        "🔗 <b>لینک و کد دعوت شما</b>\n\n"
        "<b>لینک:</b>\n<code>{link}</code>\n\n"
        "<b>کد (هنگام خرید پلن):</b>\n<code>{invite_code}</code>\n\n"
        "⚠️ لینک: هر کاربر فقط یک‌بار محاسبه می‌شود.\n"
        "⚠️ کد: فقط در <b>اولین خرید</b> هر کاربر — پس از تأیید ادمین "
        "{promo_reward_mb} مگ به شما اضافه می‌شود."
    ),
    "referral_claim_submitted": (
        "✅ درخواست اینترنت رایگان ثبت شد.\n\n"
        "کد: <code>{request_code}</code>\n"
        "مقدار: <b>{mb_display}</b>\n\n"
        "این مقدار از موجودی دعوت شما کسر شد.\n"
        "پس از بررسی ادمین، لینک Subscription برای شما ارسال می‌شود."
    ),
    "referral_claim_pending": (
        "⏳ درخواست قبلی شما هنوز در انتظار بررسی ادمین است.\n\n"
        "لطفاً تا پاسخ به درخواست اول صبر کنید."
    ),
    "referral_claim_ok": (
        "✅ درخواست <code>{request_code}</code> تأیید شد.\n\n"
        "حجم: <b>{mb_display}</b>\n\n"
        "{sub_body}"
    ),
    "referral_claim_rejected": (
        "❌ درخواست <code>{request_code}</code> رد شد.\n"
        "مقدار <b>{mb_display}</b> به موجودی دعوت شما برگشت."
    ),
    "referral_claim_insufficient": (
        "❌ موجودی {source_label} کافی نیست.\n\n"
        "حداقل لازم: <b>{claim_mb} مگابایت</b>\n"
        "موجودی شما: <b>{available_display}</b>"
    ),
    "referral_claim_insufficient_link": (
        "❌ موجودی لینک دعوت کافی نیست.\n\n"
        "حداقل <b>{claim_mb} مگابایت</b> لازم است "
        "(۲ دعوت = {reward_mb}+{reward_mb} مگ).\n\n"
        "موجودی: <b>{available_display}</b>\n"
        "دعوت موفق: <b>{invite_count}</b> نفر"
    ),
    "referral_inviter_notify": (
        "🎉 یک دوست با لینک شما عضو شد!\n\n"
        "➕ <b>{reward_mb} مگابایت</b> به موجودی لینک اضافه شد.\n"
        "💾 موجودی لینک: <b>{available_display}</b>"
    ),
    "promo_code_owner_notify": (
        "🎉 یک کاربر با کد شما پلن خرید!\n\n"
        "سفارش: <code>{order_code}</code>\n"
        "➕ <b>{reward_mb} مگابایت</b> (۵ گیگ) به موجودی کد اضافه شد.\n"
        "💾 موجودی کد: <b>{available_display}</b>"
    ),
    "promo_code_ask": (
        "🎫 <b>کد دعوت — اولین خرید</b>\n\n"
        "اگر کد دوست خود را دارید، در پیام بعدی ارسال کنید.\n"
        "این فقط برای <b>اولین خرید</b> شما است.\n"
        "برای رد کردن: {skip_hint}"
    ),
    "promo_code_not_first_buy": (
        "ℹ️ کد دعوت فقط در <b>اولین خرید</b> قابل استفاده است.\n"
        "شما قبلاً یک خرید موفق داشته‌اید."
    ),
    "promo_code_already_used": (
        "ℹ️ شما قبلاً کد دعوت را در سفارش خود ثبت کرده‌اید."
    ),
    "promo_code_invalid": "❌ کد نامعتبر است. دوباره تلاش کنید یا بدون کد ادامه دهید.",
    "promo_code_self": "❌ نمی‌توانید کد خودتان را وارد کنید.",
    "promo_code_applied": "✅ کد <code>{code}</code> ثبت شد.",
    "confirm_buy_with_code": (
        "🛒 تأیید خرید\n\n"
        "پلن: {name}\n"
        "قیمت: {price:,} تومان\n"
        "🎫 کد دعوت: <code>{promo_code}</code>\n\n"
        "آیا خرید را تأیید می‌کنید؟"
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
    "bale_sub_rejected_user": (
        "❌ درخواست اشتراک بله <code>{request_code}</code> رد شد.\n"
        "شناسه بله: <code>{bale_id}</code>\n\n"
        "در صورت اشتباه بودن شناسه، دوباره از منو «🔗 اشتراک بله» درخواست دهید."
    ),
    "admin_message_sent": "✅ پیام به کاربر <code>{user_id}</code> ارسال شد.",
    "admin_message_failed": "❌ ارسال به کاربر <code>{user_id}</code> ناموفق بود.",
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
