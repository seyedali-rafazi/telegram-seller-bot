# core/formatting.py

from html import escape

from core.messages import msg


def h(value) -> str:
    """Escape text for Telegram HTML parse_mode."""
    if value is None:
        return ""
    return escape(str(value))


def msg_e(key: str, **kwargs) -> str:
    """Persian message with HTML-escaped string arguments."""
    safe = {}
    for k, v in kwargs.items():
        if isinstance(v, (int, float)):
            safe[k] = v
        else:
            safe[k] = h(v)
    return msg(key, **safe)
