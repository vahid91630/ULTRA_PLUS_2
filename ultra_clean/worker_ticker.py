from __future__ import annotations
import time
from .config import AppConfig
from .db import DB
from .exchange import ExchangeAdapter
from .heartbeat import beat
from .logger import jlog
def main():
    cfg = AppConfig()
    if not cfg.mongo_url: raise RuntimeError("MONGO_URL لازم است")
    db = DB(cfg.mongo_url)
    cfg = AppConfig().__class__(**{**cfg.__dict__, "service_name":"worker_ticker"})
    ex = ExchangeAdapter.from_cfg(cfg.exchange, cfg.api_key, cfg.secret_key, cfg.sandbox)
    while True:
        try:
            t = ex.fetch_ticker(cfg.symbol)
            db.ticker.insert_one({"ts": int(time.time()*1000), "symbol": cfg.symbol, "tick": t})
            beat(cfg, db, "ok", price=float(t.get("last") or 0))
            jlog("info","ticker", p=float(t.get("last") or 0))
        except Exception as e:
            beat(cfg, db, "error", err=str(e))
            jlog("error","ticker_fail", err=str(e))
        time.sleep(5)
if __name__ == "__main__": main()
