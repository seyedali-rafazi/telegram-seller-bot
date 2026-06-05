# services/xui_panel.py — create test clients on 3x-ui / sanaie panel

import json
import logging
import os
import random
import string
import uuid
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)


class XuiPanelError(Exception):
    pass


def _panel_config() -> dict:
    return {
        "url": (os.getenv("XUI_PANEL_URL") or "").rstrip("/"),
        "username": os.getenv("XUI_USERNAME") or "",
        "password": os.getenv("XUI_PASSWORD") or "",
        "inbound_id": int(os.getenv("XUI_INBOUND_ID", "1")),
        "sub_url": (os.getenv("XUI_SUB_URL") or "").rstrip("/"),
        "flow": os.getenv("XUI_CLIENT_FLOW", ""),
        "traffic_mb": int(os.getenv("XUI_TEST_TRAFFIC_MB", "40")),
        "expiry_days": int(os.getenv("XUI_TEST_EXPIRY_DAYS", "0")),
        "limit_ip": int(os.getenv("XUI_LIMIT_IP", "0")),
        "verify_ssl": os.getenv("XUI_VERIFY_SSL", "true").lower()
        not in ("0", "false", "no"),
    }


def is_xui_configured() -> bool:
    cfg = _panel_config()
    return bool(cfg["url"] and cfg["username"] and cfg["password"] and cfg["sub_url"])


def _random_sub_id(length: int = 16) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


async def create_test_client(telegram_user_id: str) -> dict:
    """
    Add a one-time test client on the x-ui panel.
    Returns dict with keys: sub_url, sub_id, client_email, traffic_mb.
    """
    cfg = _panel_config()
    if not is_xui_configured():
        raise XuiPanelError("x-ui panel is not configured")

    client_email = f"tg{telegram_user_id}_test"
    client_uuid = str(uuid.uuid4())
    sub_id = _random_sub_id()
    total_bytes = cfg["traffic_mb"] * 1024 * 1024

    if cfg["expiry_days"] > 0:
        expiry_dt = datetime.now() + timedelta(days=cfg["expiry_days"])
        expiry_time = int(expiry_dt.timestamp() * 1000)
    else:
        expiry_time = 0

    client_settings = {
        "id": client_uuid,
        "email": client_email,
        "totalGB": total_bytes,
        "expiryTime": expiry_time,
        "enable": True,
        "tgId": str(telegram_user_id),
        "subId": sub_id,
        "limitIp": cfg["limit_ip"],
        "flow": cfg["flow"],
    }

    payload = {
        "id": cfg["inbound_id"],
        "settings": json.dumps({"clients": [client_settings]}),
    }

    async with httpx.AsyncClient(
        verify=cfg["verify_ssl"],
        timeout=30.0,
        follow_redirects=True,
    ) as http:
        login_resp = await http.post(
            f"{cfg['url']}/login",
            data={"username": cfg["username"], "password": cfg["password"]},
        )
        if login_resp.status_code != 200:
            logger.error("x-ui login failed: HTTP %s", login_resp.status_code)
            raise XuiPanelError("login failed")

        add_resp = await http.post(
            f"{cfg['url']}/panel/api/inbounds/addClient",
            json=payload,
        )
        if add_resp.status_code != 200:
            logger.error(
                "x-ui addClient failed: HTTP %s body=%s",
                add_resp.status_code,
                add_resp.text[:500],
            )
            raise XuiPanelError("addClient failed")

        try:
            body = add_resp.json()
        except json.JSONDecodeError:
            body = {}
        if body.get("success") is False:
            logger.error("x-ui addClient rejected: %s", add_resp.text[:500])
            raise XuiPanelError(body.get("msg") or "addClient rejected")

    sub_url = f"{cfg['sub_url']}/{sub_id}"
    return {
        "sub_url": sub_url,
        "sub_id": sub_id,
        "client_email": client_email,
        "traffic_mb": cfg["traffic_mb"],
    }
