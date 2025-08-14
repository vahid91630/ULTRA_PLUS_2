from __future__ import annotations
import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    mode: str = Field(default=os.getenv("MODE", "paper"))  # paper | live
    exchange: str = Field(default=(os.getenv("EXCHANGE") or "MEXC"))
    api_key: str = Field(default=os.getenv("MEXC_API_KEY") or os.getenv("API_KEY") or "")
    api_secret: str = Field(default=os.getenv("MEXC_API_SECRET") or os.getenv("SECRET") or "")
    db_url: str = Field(default=os.getenv("DB_URL", "").strip())
    port: int = Field(default=int(os.getenv("PORT", "8000")))

    symbol: str = Field(default=os.getenv("SYMBOL", "BTC/USDT"))
    timeframe: str = Field(default=os.getenv("TIMEFRAME", "1m"))
    base_ccy: str = Field(default=os.getenv("BASE_CCY", "USDT"))

    risk_per_trade: float = Field(default=float(os.getenv("RISK_PER_TRADE", "0.01")))
    max_usd_per_trade: float = Field(default=float(os.getenv("MAX_USD_PER_TRADE", "200")))
    max_position_usd: float = Field(default=float(os.getenv("MAX_POSITION_USD", "2000")))

    fee_bps: float = Field(default=float(os.getenv("FEE_BPS", "10")))
    slippage_bps: float = Field(default=float(os.getenv("SLIPPAGE_BPS", "5")))
    stop_loss_bps: float = Field(default=float(os.getenv("STOP_LOSS_BPS", "150")))
    take_profit_bps: float = Field(default=float(os.getenv("TAKE_PROFIT_BPS", "300")))

    heartbeat_sec: int = Field(default=int(os.getenv("HEARTBEAT_SEC", "15")))

    class Config:
        env_file = ".env"
        extra = "ignore"

SETTINGS = Settings()
