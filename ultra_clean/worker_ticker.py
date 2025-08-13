import os, time, logging
from datetime import datetime, timezone
from pymongo import MongoClient
from ultra_clean.exchange import ExchangeAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
MONGO_URL = os.getenv("MONGO_URL")

db = None
if MONGO_URL:
    db = MongoClient(MONGO_URL).get_database()
    logging.info("✅ Mongo متصل شد (ticker).")
else:
    logging.warning("⚠️ MONGO_URL نیست؛ فقط لاگ می‌نویسم (ticker).")

ex = ExchangeAdapter.from_env()
now_ms = lambda: int(datetime.now(timezone.utc).timestamp() * 1000)

def main():
    logging.info(f"🚀 worker_ticker برای {SYMBOL} شروع شد.")
    while True:
        try:
            t = ex.fetch_ticker(SYMBOL)
            last = float(t.get("last") or 0.0)
            doc = {"ts": now_ms(), "symbol": SYMBOL, "last": last, "raw": t}
            if db: db.ticker.insert_one(doc)
            logging.info(f"📈 {SYMBOL} = {last}")
        except Exception as e:
            logging.error(f"ticker error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()
