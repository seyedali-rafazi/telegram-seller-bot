# core/keyboards.py

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from core.constants import (
    BTN_BUY,
    BTN_ACCOUNT,
    BTN_MY_ORDERS,
    BTN_WALLET,
    BTN_SUPPORT,
    BTN_BALE_SUB,
    BTN_TEST,
    BTN_REFERRAL,
    BTN_BACK,
    SUPPORT_URL,
)
from core.messages import msg


def get_main_menu_keyboard():
    keyboard = [
        [
            KeyboardButton(BTN_BUY, style="success"),
            KeyboardButton(BTN_ACCOUNT, style="primary"),
        ],
        [KeyboardButton(BTN_MY_ORDERS), KeyboardButton(BTN_WALLET)],
        [KeyboardButton(BTN_BALE_SUB), KeyboardButton(BTN_TEST)],
        [KeyboardButton(BTN_REFERRAL), KeyboardButton(BTN_SUPPORT)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_back_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton(BTN_BACK)]], resize_keyboard=True)


def get_plans_keyboard(plans):
    rows = []
    for plan in plans:
        pid, name, days, gb, price = plan[0], plan[1], plan[2], plan[3], plan[4]
        label = msg("plan_item", name=name, days=days, gb=gb, price=price)
        rows.append([InlineKeyboardButton(label[:60], callback_data=f"plan_{pid}")])
    return InlineKeyboardMarkup(rows)


def get_confirm_purchase_keyboard(plan_id: int, *, show_promo: bool = True):
    rows = [
        [InlineKeyboardButton("✅ تأیید", callback_data=f"buy_confirm_{plan_id}")],
    ]
    if show_promo:
        rows.append(
            [
                InlineKeyboardButton(
                    "🎫 کد دعوت (اولین خرید)", callback_data=f"buy_promo_{plan_id}"
                )
            ]
        )
    rows.append([InlineKeyboardButton("❌ انصراف", callback_data="buy_cancel")])
    return InlineKeyboardMarkup(rows)


def get_support_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(msg("contact_admin"), url=SUPPORT_URL)]]
    )


def get_admin_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👥 کاربران", callback_data="adm_users")],
            [
                InlineKeyboardButton("💳 تأیید پرداخت‌ها", callback_data="adm_payments"),
                InlineKeyboardButton("🛒 سفارش‌ها", callback_data="adm_orders"),
            ],
            [
                InlineKeyboardButton("🔗 اشتراک بله", callback_data="adm_bale_requests"),
                InlineKeyboardButton("🎁 دعوت", callback_data="adm_referral_requests"),
            ],
            [InlineKeyboardButton("📦 مدیریت پلن‌ها", callback_data="adm_plans")],
            [
                InlineKeyboardButton("🔗 ساب پولی", callback_data="adm_configs"),
                InlineKeyboardButton("🧪 ساب تست", callback_data="adm_test_configs"),
            ],
            [InlineKeyboardButton("📢 پیام همگانی", callback_data="adm_broadcast")],
            [InlineKeyboardButton("📊 آمار", callback_data="adm_stats")],
        ]
    )
