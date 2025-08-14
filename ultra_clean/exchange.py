# path: ultra_clean/exchange.py
from __future__ import annotations
import os
import ccxt

def _make_client(name: str, api: str, sec: str):
    cls = getattr(ccxt, name, None) or getattr(ccxt, "mexc", None) or getattr(ccxt, "mexc3", None)
    if cls is None:
        raise RuntimeError(f"Unsupported exchange id: {name}")
    return cls({
        "apiKey": api or "",
        "secret": sec or "",
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })

def build_exchange(name: str, api: str, sec: str):
    """
    برمی‌گرداند: نمونهٔ اکسچنج ccxt با گارد سندباکس.
    برای MEXC هرگز sandbox فعال نمی‌شود چون test URL ندارد.
    """
    ex_id = (name or "mexc").lower()
    ex = _make_client(ex_id, api, sec)

    sandbox_env = os.getenv("SANDBOX", "false").strip().lower() in {"1", "true", "yes", "on"}
    # فقط اگر: 1) کاربر سندباکس خواسته 2) اکسچنج تست‌نت دارد 3) mexc/mexc3 نیست
    if sandbox_env:
        try:
            urls = getattr(ex, "urls", {}) or {}
            has_test = bool(urls.get("test"))
            if has_test and getattr(ex, "id", ex_id) not in {"mexc", "mexc3"} and hasattr(ex, "set_sandbox_mode"):
                ex.set_sandbox_mode(True)
            # اگر یکی از شرایط نبود، به‌صورت امن نادیده بگیر
        except Exception:
            pass

    ex.load_markets()
    return ex
