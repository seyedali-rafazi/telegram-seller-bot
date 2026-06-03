# core/keyboards.py

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from core.i18n import t


def get_main_menu_keyboard(lang: str = "fa"):
    keyboard = [
        [KeyboardButton(t(lang, "btn_buy")), KeyboardButton(t(lang, "btn_account"))],
        [KeyboardButton(t(lang, "btn_wallet")), KeyboardButton(t(lang, "btn_support"))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_back_keyboard(lang: str = "fa"):
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t(lang, "btn_back"))]], resize_keyboard=True
    )


def get_language_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            ]
        ]
    )


def get_plans_keyboard(plans, lang: str = "fa"):
    rows = []
    for plan in plans:
        pid, name, days, gb, price = plan[0], plan[1], plan[2], plan[3], plan[4]
        label = t(lang, "plan_item", name=name, days=days, gb=gb, price=price)
        rows.append([InlineKeyboardButton(label[:60], callback_data=f"plan_{pid}")])
    return InlineKeyboardMarkup(rows)


def get_confirm_purchase_keyboard(plan_id: int, lang: str = "fa"):
    yes = "✅ تأیید" if lang == "fa" else "✅ Confirm"
    no = "❌ انصراف" if lang == "fa" else "❌ Cancel"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(yes, callback_data=f"buy_confirm_{plan_id}"),
                InlineKeyboardButton(no, callback_data="buy_cancel"),
            ]
        ]
    )


def get_support_keyboard(lang: str = "fa"):
    from core.constants import SUPPORT_URL

    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t(lang, "contact_admin"), url=SUPPORT_URL)],
        ]
    )


def get_admin_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👥 کاربران", callback_data="adm_users")],
            [
                InlineKeyboardButton(
                    "💳 تأیید پرداخت‌ها", callback_data="adm_payments"
                )
            ],
            [InlineKeyboardButton("📦 مدیریت پلن‌ها", callback_data="adm_plans")],
            [InlineKeyboardButton("🔗 کانفیگ‌ها", callback_data="adm_configs")],
            [InlineKeyboardButton("📢 پیام همگانی", callback_data="adm_broadcast")],
            [InlineKeyboardButton("📊 آمار", callback_data="adm_stats")],
        ]
    )
