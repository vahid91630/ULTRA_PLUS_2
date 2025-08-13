from __future__ import annotations
import os
from dataclasses import dataclass
def _bool(x: str|None, default: bool=False)->bool:
    if x is None: return default
    return x.strip().lower() in {"1","true","yes","on"}
@dataclass(frozen=True)
class AppConfig:
    mongo_url: str|None = os.getenv("MONGO_URL")
    exchange: str = os.getenv("EXCHANGE","mexc")
    api_key: str|None = os.getenv("EXCHANGE_API_KEY")
    secret_key: str|None = os.getenv("EXCHANGE_SECRET_KEY")
    sandbox: bool = _bool(os.getenv("SANDBOX"), True)
    symbol: str = os.getenv("SYMBOL","BTC/USDT")
    timeframe: str = os.getenv("TIMEFRAME","1m")
    app_ver: str = os.getenv("APP_VER","v1")
    service_name: str = os.getenv("SERVICE_NAME","web")
