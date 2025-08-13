import os
import ccxt

class ExchangeAdapter:
    def __init__(self, ex: ccxt.Exchange):
        self.ex = ex
        self._markets_loaded = False

    @classmethod
    def from_env(cls):
        name = os.getenv("EXCHANGE","mexc").lower()
        api  = os.getenv("API_KEY") or ""
        sec  = os.getenv("SECRET") or ""
        sandbox = os.getenv("SANDBOX","true").lower() in {"1","true","yes","on"}
        if name == "mexc":
            ex = ccxt.mexc({"apiKey": api, "secret": sec, "enableRateLimit": True})
        else:
            ex = getattr(ccxt, name)({"apiKey": api, "secret": sec, "enableRateLimit": True})
        if sandbox and hasattr(ex, "set_sandbox_mode"):
            try: ex.set_sandbox_mode(True)
            except: pass
        return cls(ex)

    def _ensure_markets(self):
        if not self._markets_loaded:
            self.ex.load_markets()
            self._markets_loaded = True

    def fetch_ticker(self, symbol: str):
        self._ensure_markets()
        try:
            return self.ex.fetch_ticker(symbol)
        except ccxt.NotSupported:
            o = self.fetch_ohlcv(symbol, timeframe="1m", limit=1) or []
            last = o[-1][4] if o else None
            return {"symbol": symbol, "last": last}

    def fetch_ohlcv(self, symbol: str, timeframe="1m", limit=200):
        self._ensure_markets()
        return self.ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def create_market_order(self, symbol: str, side: str, amount: float):
        self._ensure_markets()
        return self.ex.create_order(symbol, type="market", side=side, amount=amount)
