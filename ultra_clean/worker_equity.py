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
    cfg = AppConfig().__class__(**{**cfg.__dict__, "service_name":"worker_equity"})
    ex = ExchangeAdapter.from_cfg(cfg.exchange, cfg.api_key, cfg.secret_key, cfg.sandbox)
    while True:
        try:
            bal = ex.fetch_balance() or {}
            total = (bal.get("total") or {}).get("USDT") or 0.0
            db.equity.insert_one({"ts": int(time.time()*1000), "equity": float(total), "source": "balance"})
            beat(cfg, db, "ok", equity=float(total))
            jlog("info","equity", eq=float(total))
        except Exception as e:
            beat(cfg, db, "error", err=str(e))
            jlog("error","equity_fail", err=str(e))
        time.sleep(15)
if __name__ == "__main__": main()
