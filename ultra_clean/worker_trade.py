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
    cfg = AppConfig().__class__(**{**cfg.__dict__, "service_name":"worker_trade"})
    ex = ExchangeAdapter.from_cfg(cfg.exchange, cfg.api_key, cfg.secret_key, cfg.sandbox)
    while True:
        try:
            sig = db.signals.find_one(sort=[("ts",-1)])
            if not sig or int(time.time()) > int(sig.get("ttl",0)):
                beat(cfg, db, "ok", idle=True); time.sleep(2); continue
            side = sig["ens"]["side"]
            if side == "hold":
                beat(cfg, db, "ok", hold=True); time.sleep(2); continue
            t = ex.fetch_ticker(cfg.symbol)
            px = float(t.get("last") or 0.0) or 0.0
            usd = 20.0
            amt = usd / max(px,1e-9)
            try:
                ex.create_market_order(cfg.symbol, side, amt)
                db.trades.insert_one({"ts": int(time.time()*1000), "symbol": cfg.symbol, "side": side, "price": px, "amount": amt, "usd": usd})
                beat(cfg, db, "ok", traded=side, usd=usd)
                jlog("info","trade_ok", side=side, usd=usd)
            except Exception as e:
                beat(cfg, db, "error", err=str(e))
                jlog("error","trade_fail", err=str(e))
        except Exception as e:
            beat(cfg, db, "error", err=str(e))
            jlog("error","loop_fail", err=str(e))
        time.sleep(3)
if __name__ == "__main__": main()
