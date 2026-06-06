# core/constants.py

import os

SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/admin")
ADMIN_ID = os.getenv("ADMIN_ID", "")
CARD_NUMBER = os.getenv("CARD_NUMBER", "")
CARD_HOLDER = os.getenv("CARD_HOLDER", "VPN Bot")

# دکمه‌های منو (فارسی)
BTN_BUY = "🛒 خرید پلن"
BTN_ACCOUNT = "👤 حساب من"
BTN_MY_ORDERS = "📋 سفارش‌ها و ساب"
BTN_SUPPORT = "📖 راهنما و پشتیبانی"
BTN_BALE_SUB = "🔗 اشتراک بله"
BTN_TEST = "🧪 تست"
BTN_REFERRAL = "🎁 دعوت دوستان"
BTN_BACK = "🔙 بازگشت"

REFERRAL_REWARD_MB = 500
REFERRAL_CLAIM_MB = 1000
PROMO_CODE_REWARD_MB = 5000
PROMO_CODE_CLAIM_MB = 5000

# State steps
STATE_PURCHASE_RECEIPT = "purchase_receipt"
STATE_BALE_ID = "bale_id"
STATE_PURCHASE_PROMO_CODE = "purchase_promo_code"
STATE_ADMIN_BROADCAST = "admin_broadcast"
STATE_ADMIN_CONFIGS = "admin_configs"
STATE_ADMIN_TEST_CONFIGS = "admin_test_configs"
STATE_ADMIN_PLAN_NAME = "admin_plan_name"
STATE_ADMIN_PLAN_DAYS = "admin_plan_days"
STATE_ADMIN_PLAN_GB = "admin_plan_gb"
STATE_ADMIN_PLAN_PRICE = "admin_plan_price"
STATE_ADMIN_USER_BALANCE = "admin_user_balance"
STATE_ADMIN_ORDER_CONFIG = "admin_order_config"
STATE_ADMIN_BALE_SUB = "admin_bale_sub"
STATE_ADMIN_REFERRAL_SUB = "admin_referral_sub"
