# core/constants.py

import os

SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/admin")
ADMIN_ID = os.getenv("ADMIN_ID", "")
CARD_NUMBER = os.getenv("CARD_NUMBER", "")
CARD_HOLDER = os.getenv("CARD_HOLDER", "VPN Bot")

# دکمه‌های منو (فارسی)
BTN_BUY = "🛒 خرید پلن"
BTN_ACCOUNT = "👤 حساب من"
BTN_WALLET = "💳 شارژ کیف پول"
BTN_SUPPORT = "📖 راهنما و پشتیبانی"
BTN_BACK = "🔙 بازگشت"

# State steps
STATE_WALLET_AMOUNT = "wallet_amount"
STATE_WALLET_RECEIPT = "wallet_receipt"
STATE_ADMIN_BROADCAST = "admin_broadcast"
STATE_ADMIN_CONFIGS = "admin_configs"
STATE_ADMIN_PLAN_NAME = "admin_plan_name"
STATE_ADMIN_PLAN_DAYS = "admin_plan_days"
STATE_ADMIN_PLAN_GB = "admin_plan_gb"
STATE_ADMIN_PLAN_PRICE = "admin_plan_price"
STATE_ADMIN_USER_BALANCE = "admin_user_balance"
STATE_ADMIN_ORDER_CONFIG = "admin_order_config"
