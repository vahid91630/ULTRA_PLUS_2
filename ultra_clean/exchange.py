from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import ccxt
@dataclass
class ExchangeAdapter:
    client: Any
    name: str
    @classmethod
    def from_cfg(cls, name: str, api_key: Optional[str], secret: Optional[str], sandbox: bool=True) -> "ExchangeAdapter":
        n = (name or "mexc").lower()
        if n not in ccxt.exchanges:
            raise ValueError(f"Unsupported exchange: {n}")
        klass = getattr(ccxt, n)
        client = klass({"apiKey": api_key, "secret": secret, "enableRateLimit": True})
        if sandbox and hasattr(client, "set_sandbox_mode"):
            client.set_sandbox_mode(True)
        return cls(client=client, name=n)
    def fetch_ticker(self, symbol: str) -> Dict[str,any]:
        return self.client.fetch_ticker(symbol)
    def fetch_balance(self):
        return self.client.fetch_balance()
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int=200):
        return self.client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    def create_market_order(self, symbol: str, side: str, amount: float):
        return self.client.create_order(symbol, "market", side, amount)
