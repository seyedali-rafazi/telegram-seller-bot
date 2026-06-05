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
    """Panel API rejected the request or returned an error."""

    pass


class XuiPanelConnectionError(XuiPanelError):
    """Bot could not reach the panel (timeout, refused, DNS, etc.)."""

    pass


def _panel_config() -> dict:
    timeout = float(os.getenv("XUI_TIMEOUT_SECONDS", "60"))
    proxy = os.getenv("XUI_PROXY") or os.getenv("PROXY") or None
    return {
        "url": (os.getenv("XUI_PANEL_URL") or "").rstrip("/"),
        "url_local": (os.getenv("XUI_PANEL_URL_LOCAL") or "").rstrip("/"),
        "username": os.getenv("XUI_USERNAME") or "",
        "password": os.getenv("XUI_PASSWORD") or "",
        "two_factor_code": os.getenv("XUI_TWO_FACTOR_CODE") or "",
        "inbound_id": int(os.getenv("XUI_INBOUND_ID", "1")),
        "sub_url": (os.getenv("XUI_SUB_URL") or "").rstrip("/"),
        "flow": os.getenv("XUI_CLIENT_FLOW", ""),
        "traffic_mb": int(os.getenv("XUI_TEST_TRAFFIC_MB", "40")),
        "expiry_days": int(os.getenv("XUI_TEST_EXPIRY_DAYS", "0")),
        "limit_ip": int(os.getenv("XUI_LIMIT_IP", "0")),
        "verify_ssl": os.getenv("XUI_VERIFY_SSL", "true").lower()
        not in ("0", "false", "no"),
        "timeout": httpx.Timeout(timeout, connect=min(timeout, 20.0)),
        "proxy": proxy,
    }


def is_xui_configured() -> bool:
    cfg = _panel_config()
    return bool(cfg["url"] and cfg["username"] and cfg["password"] and cfg["sub_url"])


def _random_sub_id(length: int = 16) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


def _panel_urls_to_try(cfg: dict) -> list[str]:
    urls = []
    if cfg["url"]:
        urls.append(cfg["url"])
    if cfg["url_local"] and cfg["url_local"] not in urls:
        urls.append(cfg["url_local"])
    return urls


def _connection_error(panel_url: str, exc: Exception) -> XuiPanelConnectionError:
    logger.error(
        "x-ui connection failed for %s: %s: %s",
        panel_url,
        type(exc).__name__,
        exc,
    )
    hint = (
        "If the bot runs on the same server as the panel, set "
        "XUI_PANEL_URL_LOCAL=http://127.0.0.1:PORT/your-path in .env"
    )
    return XuiPanelConnectionError(
        f"cannot connect to panel at {panel_url} ({type(exc).__name__}). {hint}"
    )


def _login_payload(cfg: dict) -> dict:
    payload = {
        "username": cfg["username"],
        "password": cfg["password"],
    }
    if cfg["two_factor_code"]:
        payload["twoFactorCode"] = cfg["two_factor_code"]
    return payload


def _parse_api_response(resp: httpx.Response) -> dict:
    try:
        return resp.json()
    except json.JSONDecodeError:
        return {}


async def _login(http: httpx.AsyncClient, panel_url: str, cfg: dict) -> None:
    try:
        login_resp = await http.post(
            f"{panel_url}/login",
            json=_login_payload(cfg),
        )
    except (httpx.ConnectTimeout, httpx.ConnectError, httpx.ReadTimeout) as exc:
        raise _connection_error(panel_url, exc) from exc

    body = _parse_api_response(login_resp)
    if login_resp.status_code != 200 or body.get("success") is False:
        logger.error(
            "x-ui login failed for %s: HTTP %s body=%s",
            panel_url,
            login_resp.status_code,
            login_resp.text[:300],
        )
        raise XuiPanelError(body.get("msg") or "login failed")


async def _create_test_client_on_panel(
    panel_url: str, cfg: dict, payload: dict
) -> None:
    async with httpx.AsyncClient(
        verify=cfg["verify_ssl"],
        timeout=cfg["timeout"],
        follow_redirects=True,
        proxy=cfg["proxy"],
    ) as http:
        await _login(http, panel_url, cfg)

        try:
            add_resp = await http.post(
                f"{panel_url}/panel/api/inbounds/addClient",
                json=payload,
            )
        except (httpx.ConnectTimeout, httpx.ConnectError, httpx.ReadTimeout) as exc:
            raise _connection_error(panel_url, exc) from exc

        if add_resp.status_code != 200:
            logger.error(
                "x-ui addClient failed for %s: HTTP %s body=%s",
                panel_url,
                add_resp.status_code,
                add_resp.text[:500],
            )
            raise XuiPanelError("addClient failed")

        body = _parse_api_response(add_resp)
        if body.get("success") is False:
            logger.error(
                "x-ui addClient rejected for %s: %s",
                panel_url,
                add_resp.text[:500],
            )
            raise XuiPanelError(body.get("msg") or "addClient rejected")


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

    panel_urls = _panel_urls_to_try(cfg)
    if not panel_urls:
        raise XuiPanelError("x-ui panel URL is not set")

    last_connection_error: XuiPanelConnectionError | None = None
    for panel_url in panel_urls:
        try:
            await _create_test_client_on_panel(panel_url, cfg, payload)
            if panel_url != cfg["url"]:
                logger.info("x-ui API succeeded via fallback URL %s", panel_url)
            break
        except XuiPanelConnectionError as exc:
            last_connection_error = exc
            if panel_url != panel_urls[-1]:
                logger.warning(
                    "x-ui primary URL failed, trying fallback: %s", panel_urls[-1]
                )
                continue
            raise
    else:
        if last_connection_error:
            raise last_connection_error
        raise XuiPanelError("x-ui panel request failed")

    sub_url = f"{cfg['sub_url']}/{sub_id}"
    return {
        "sub_url": sub_url,
        "sub_id": sub_id,
        "client_email": client_email,
        "traffic_mb": cfg["traffic_mb"],
    }
