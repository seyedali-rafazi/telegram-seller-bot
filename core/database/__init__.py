# core/database/__init__.py

from .base import DB_NAME
from .utils import get_tehran_today, get_tehran_now_full
from .init_db import init_db
from .settings import get_setting, set_setting
from .users import (
    add_user,
    get_user_info,
    get_full_user_info,
    get_total_users,
    get_all_users,
    is_user_banned,
    set_user_banned,
    search_users_page,
)
from .plans import (
    get_active_plans,
    get_all_plans,
    get_plan,
    create_plan,
    update_plan,
    delete_plan,
)
from .wallet import get_wallet_balance, adjust_wallet, set_wallet_balance
from .payments import (
    create_payment_request,
    get_payment,
    get_pending_payments,
    count_pending_payments,
    approve_payment,
    reject_payment,
)
from .configs import add_configs_bulk, count_available_configs, count_total_configs
from .subscriptions import get_active_subscriptions, get_user_pending_orders
from .user_orders import (
    get_user_pending_orders_detailed,
    get_user_orders_history,
    count_user_orders_by_status,
    get_user_subscriptions_all,
    get_subscription_by_id,
)
from .orders import (
    create_purchase_order,
    get_order,
    get_pending_orders,
    count_pending_orders,
    reject_purchase_order,
    fulfill_purchase_order,
)
