from __future__ import annotations
import time
from statistics import mean
from .config import AppConfig
from .db import DB
from .exchange import ExchangeAdapter
from .heartbeat import beat
from .logger import jlog
FAST=9; SLOW=21
def sma(values, n):
    return (sum(values[-n:])/n) if len(values)>=n else None
def main():
    cfg = AppConfig()
    if not cfg.mongo_url: raise RuntimeError("MONGO_URL لازم است")
    db = DB(cfg.mongo_url)
    cfg = AppConfig().__class__(**{**cfg.__dict__, "service_name":"worker_signal"})
    ex = ExchangeAdapter.from_cfg(cfg.exchange, cfg.api_key, cfg.secret_key, cfg.sandbox)
    pf = ps = None
    while True:
        try:
            ohl = ex.fetch_ohlcv(cfg.symbol, cfg.timeframe, limit=max(SLOW+5, 50))
            closes = [x[4] for x in ohl]
            f = sma(closes, FAST); s = sma(closes, SLOW)
            side = "hold"
            if f and s and pf is not None and ps is not None:
                if pf <= ps and f > s: side = "buy"
                elif pf >= ps and f < s: side = "sell"
            pf, ps = f, s
            db.signals.insert_one({"ts": int(time.time()*1000), "symbol": cfg.symbol, "ens": {"side": side, "score": 0.6 if side!='hold' else 0.0}, "ttl": int(time.time())+180})
            beat(cfg, db, "ok", side=side)
            jlog("info","signal", side=side)
        except Exception as e:
            beat(cfg, db, "error", err=str(e))
            jlog("error","signal_fail", err=str(e))
        time.sleep(10)
if __name__ == "__main__": main()
