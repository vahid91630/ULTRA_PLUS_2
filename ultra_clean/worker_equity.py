import os, time, logging
from datetime import datetime, timezone
from pymongo import MongoClient
from ultra_clean.exchange import ExchangeAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
BASE_CCY = os.getenv("EQUITY_CCY", "USDT")
MONGO_URL = os.getenv("MONGO_URL")

db = MongoClient(MONGO_URL).get_database() if MONGO_URL else None
if db: logging.info("✅ Mongo متصل شد (equity).")
else:  logging.warning("⚠️ MONGO_URL نیست؛ فقط لاگ می‌نویسم (equity).")

ex = ExchangeAdapter.from_env()
now_ms = lambda: int(datetime.now(timezone.utc).timestamp() * 1000)

def main():
    logging.info("🚀 worker_equity شروع شد.")
    while True:
        try:
            bal = ex.ex.fetch_balance()
            total = 0.0
            if "total" in bal and isinstance(bal["total"], dict):
                total = float(bal["total"].get(BASE_CCY, 0.0))
            doc = {"ts": now_ms(), "ccy": BASE_CCY, "equity": total}
            if db: db.equity.insert_one(doc)
            logging.info(f"💼 Equity {BASE_CCY} = {total}")
        except Exception as e:
            logging.error(f"equity error: {e}")
        time.sleep(15)

if __name__ == "__main__":
    main()
