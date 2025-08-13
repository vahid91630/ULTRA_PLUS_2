import os, time, logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Mongo (ایمن: اگر بد/غلط بود، سرویس نمی‌میرد)
db = None
MONGO_URL = os.getenv("MONGO_URL")
if MONGO_URL:
    try:
        from pymongo import MongoClient
        db = MongoClient(MONGO_URL, serverSelectionTimeoutMS=4000).get_database()
        _ = db.name  # touch
        logging.info("✅ Mongo متصل شد (ticker).")
    except Exception as e:
        db = None
        logging.warning(f"⚠️ اتصال Mongo ناموفق؛ ادامه بدون ذخیره. {e}")

# Exchange (ایمن)
from ultra_clean.exchange import ExchangeAdapter
try:
    ex = ExchangeAdapter.from_env()
    logging.info(f"✅ اتصال صرافی: {ex.ex.id}")
except Exception as e:
    logging.error(f"❌ اتصال صرافی ناموفق: {e}")
    ex = None

SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
now_ms = lambda: int(datetime.now(timezone.utc).timestamp() * 1000)

def main():
    logging.info(f"🚀 worker_ticker برای {SYMBOL} شروع شد.")
    while True:
        try:
            if not ex:
                time.sleep(3); continue
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
