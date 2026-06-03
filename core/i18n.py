# core/i18n.py

TEXTS = {
    "fa": {
        "welcome": (
            "👋 به ربات VPN خوش آمدید!\n\n"
            "از منوی زیر گزینه مورد نظر را انتخاب کنید.\n"
            "زبان را می‌توانید با دکمه‌های زیر تغییر دهید."
        ),
        "choose_lang": "🌐 زبان را انتخاب کنید:",
        "lang_set": "✅ زبان به فارسی تغییر کرد.",
        "banned": "🚫 حساب شما مسدود شده است. با پشتیبانی تماس بگیرید.",
        "btn_buy": "🛒 خرید پلن",
        "btn_account": "👤 حساب من",
        "btn_wallet": "💳 شارژ کیف پول",
        "btn_support": "📖 راهنما و پشتیبانی",
        "btn_back": "🔙 بازگشت",
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
        "no_configs": "❌ در حال حاضر کانفیگ آماده‌ای موجود نیست. لطفاً بعداً تلاش کنید.",
        "purchase_ok": (
            "✅ خرید با موفقیت انجام شد!\n\n"
            "پلن: {name}\n"
            "اعتبار تا: {expires}\n\n"
            "🔗 کانفیگ VPN شما:\n\n"
            "`{config}`"
        ),
        "account_title": "👤 **حساب کاربری**",
        "account_body": (
            "🆔 شناسه: `{uid}`\n"
            "👤 نام کاربری: {username}\n"
            "💰 موجودی کیف پول: **{balance:,}** تومان\n"
            "📅 عضویت از: {join_date}\n\n"
            "**سرویس‌های فعال:**\n{services}"
        ),
        "no_active_service": "— هیچ سرویس فعالی ندارید —",
        "service_line": "• {name} — تا {expires}",
        "wallet_intro": (
            "💳 **شارژ کیف پول (کارت به کارت)**\n\n"
            "۱. مبلغ را به شماره کارت زیر واریز کنید:\n"
            "`{card}`\n"
            "به نام: {card_name}\n\n"
            "۲. مبلغ واریزی (به تومان) را در پیام بعدی ارسال کنید.\n"
            "۳. سپس عکس رسید را آپلود کنید.\n\n"
            "پس از تأیید ادمین، موجودی شما شارژ می‌شود."
        ),
        "enter_amount": "💰 مبلغ واریزی را به **تومان** (فقط عدد) ارسال کنید:",
        "invalid_amount": "❌ مبلغ نامعتبر است. یک عدد صحیح بزرگ‌تر از صفر وارد کنید.",
        "upload_receipt": "📸 لطفاً عکس رسید واریز را ارسال کنید:",
        "receipt_submitted": (
            "✅ درخواست شارژ ثبت شد.\n"
            "مبلغ: {amount:,} تومان\n\n"
            "پس از بررسی ادمین، موجودی شما به‌روز می‌شود."
        ),
        "support_guide": (
            "📖 **راهنمای اتصال VPN**\n\n"
            "**اندروید:**\n"
            "۱. اپ v2rayNG یا Hiddify را نصب کنید.\n"
            "۲. کانفیگ دریافتی را کپی کنید.\n"
            "۳. از منو Import from clipboard را بزنید.\n"
            "۴. اتصال را فعال کنید.\n\n"
            "**iOS:**\n"
            "۱. Streisand یا V2Box را از App Store نصب کنید.\n"
            "۲. لینک کانفیگ را import کنید.\n"
            "۳. Allow VPN Configuration را تأیید کنید.\n\n"
            "برای سوالات بیشتر با ادمین تماس بگیرید."
        ),
        "contact_admin": "💬 تماس با ادمین",
    },
    "en": {
        "welcome": (
            "👋 Welcome to the VPN Bot!\n\n"
            "Choose an option from the menu below.\n"
            "You can change language with the buttons below."
        ),
        "choose_lang": "🌐 Choose your language:",
        "lang_set": "✅ Language set to English.",
        "banned": "🚫 Your account is banned. Contact support.",
        "btn_buy": "🛒 Buy Plan",
        "btn_account": "👤 My Account",
        "btn_wallet": "💳 Top Up Wallet",
        "btn_support": "📖 Help & Support",
        "btn_back": "🔙 Back",
        "plans_title": "📦 Available plans:\n\nTap a plan to purchase:",
        "no_plans": "❌ No plans available at the moment.",
        "plan_item": "{name}\n⏱ {days} days | 📊 {gb} GB | 💰 {price:,} Toman",
        "confirm_buy": (
            "🛒 Confirm purchase\n\n"
            "Plan: {name}\n"
            "Price: {price:,} Toman\n"
            "Wallet balance: {balance:,} Toman\n\n"
            "Confirm purchase?"
        ),
        "insufficient_balance": (
            "❌ Insufficient wallet balance.\n"
            "Required: {price:,} Toman — Balance: {balance:,} Toman\n\n"
            "Use «Top Up Wallet» from the menu."
        ),
        "no_configs": "❌ No VPN configs available right now. Please try later.",
        "purchase_ok": (
            "✅ Purchase successful!\n\n"
            "Plan: {name}\n"
            "Valid until: {expires}\n\n"
            "🔗 Your VPN config:\n\n"
            "`{config}`"
        ),
        "account_title": "👤 **My Account**",
        "account_body": (
            "🆔 ID: `{uid}`\n"
            "👤 Username: {username}\n"
            "💰 Wallet: **{balance:,}** Toman\n"
            "📅 Member since: {join_date}\n\n"
            "**Active services:**\n{services}"
        ),
        "no_active_service": "— No active services —",
        "service_line": "• {name} — until {expires}",
        "wallet_intro": (
            "💳 **Wallet top-up (card to card)**\n\n"
            "1. Transfer to this card:\n"
            "`{card}`\n"
            "Name: {card_name}\n\n"
            "2. Send the amount (Toman) in the next message.\n"
            "3. Upload a photo of the receipt.\n\n"
            "Balance is credited after admin approval."
        ),
        "enter_amount": "💰 Send the transfer amount in **Toman** (numbers only):",
        "invalid_amount": "❌ Invalid amount. Enter a positive integer.",
        "upload_receipt": "📸 Please upload a photo of your payment receipt:",
        "receipt_submitted": (
            "✅ Top-up request submitted.\n"
            "Amount: {amount:,} Toman\n\n"
            "Your balance will update after admin review."
        ),
        "support_guide": (
            "📖 **VPN connection guide**\n\n"
            "**Android:**\n"
            "1. Install v2rayNG or Hiddify.\n"
            "2. Copy your config link.\n"
            "3. Import from clipboard.\n"
            "4. Connect.\n\n"
            "**iOS:**\n"
            "1. Install Streisand or V2Box.\n"
            "2. Import the config link.\n"
            "3. Allow VPN configuration.\n\n"
            "Contact admin for more help."
        ),
        "contact_admin": "💬 Contact admin",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in TEXTS else "fa"
    text = TEXTS[lang].get(key, TEXTS["fa"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text
