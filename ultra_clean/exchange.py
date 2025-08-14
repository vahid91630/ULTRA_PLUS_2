# path: ultra_clean/exchange.py
from __future__ import annotations
import os
import ccxt
from typing import Tuple

def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name, str(default)).strip().lower()
    return v in {"1", "true", "yes", "on"}

def _make_client(ex_id: str, api: str, sec: str):
    ex_id = (ex_id or "mexc").lower()
    cls = getattr(ccxt, ex_id, None) or getattr(ccxt, "mexc", None) or getattr(ccxt, "mexc3", None)
    if not cls:
        raise RuntimeError(f"Unsupported exchange id: {ex_id}")
    return cls({
        "apiKey": api or "",
        "secret": sec or "",
        "enableRateLimit": True,
        "options": {
            "defaultType": "spot",
            "adjustForTimeDifference": True,  # چرا: امضا به‌خاطر اختلاف زمان رد نشود
        },
    })

def build_exchange(ex_id: str, api: str, sec: str):
    ex = _make_client(ex_id, api, sec)

    # هرگز برای MEXC sandbox نزن
    sandbox = _bool_env("SANDBOX", False)
    if sandbox and getattr(ex, "id", "mexc") not in {"mexc", "mexc3"}:
        try:
            if getattr(ex, "urls", {}).get("test") and hasattr(ex, "set_sandbox_mode"):
                ex.set_sandbox_mode(True)
        except Exception:
            pass

    ex.load_markets()
    return ex

def verify_auth(ex) -> Tuple[bool, str | None]:
    """صحت کلیدها را چک می‌کند؛ اگر خطا باشد، پیام دقیق برمی‌گرداند."""
    try:
        # Sync اختلاف ساعت با صرافی
        if hasattr(ex, "load_time_difference"):
            ex.load_time_difference()
        # یک کال خصوصی سبک برای تست امضا/کلید
        ex.fetch_balance(params={"recvWindow": 50000})
        return True, None
    except Exception as e:
        return False, str(e)
