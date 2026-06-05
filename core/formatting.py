# core/formatting.py

from html import escape

from core.messages import msg


def h(value) -> str:
    """Escape text for Telegram HTML parse_mode."""
    if value is None:
        return ""
    return escape(str(value))


# Placeholders that already contain Telegram HTML from format_sub_delivery etc.
_RAW_HTML_KEYS = frozenset({"sub_body"})


def msg_e(key: str, **kwargs) -> str:
    """Persian message with HTML-escaped string arguments."""
    safe = {}
    for k, v in kwargs.items():
        if k in _RAW_HTML_KEYS:
            safe[k] = v
        elif isinstance(v, (int, float)):
            safe[k] = v
        else:
            safe[k] = h(v)
    return msg(key, **safe)


def format_sub_delivery(sub_url: str) -> str:
    return msg_e("sub_link_body", sub_url=sub_url)
