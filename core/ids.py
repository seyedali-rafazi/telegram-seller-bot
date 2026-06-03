# core/ids.py — شناسه یکتای قابل نمایش برای پرداخت و سفارش


def payment_public_id(db_id: int) -> str:
    return f"PAY-{db_id:08d}"


def order_public_id(db_id: int) -> str:
    return f"ORD-{db_id:08d}"


def subscription_public_id(db_id: int) -> str:
    return f"SUB-{db_id:08d}"
