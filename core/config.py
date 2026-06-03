# core/config.py — بارگذاری تنظیمات از .env (قبل از هر import دیگر main را با load_dotenv شروع کنید)

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _split_ids(raw: str) -> list[str]:
    ids = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip().strip('"').strip("'")
        if part:
            ids.append(part)
    return ids


def get_admin_ids() -> list[str]:
    """شناسه عددی ادمین(ها) از ADMIN_ID یا ADMIN_IDS (با ویرگول)."""
    raw = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID") or ""
    return _split_ids(raw)


def get_primary_admin_id() -> str:
    """اولین ادمین — برای state پنل ادمین."""
    ids = get_admin_ids()
    return ids[0] if ids else ""


def is_admin_chat(chat_id) -> bool:
    return str(chat_id) in get_admin_ids()
