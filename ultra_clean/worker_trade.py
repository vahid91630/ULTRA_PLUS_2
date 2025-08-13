import os, time, logging, traceback
from pymongo import MongoClient
from ultra_clean.exchange import ExchangeAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

API_KEY = os.getenv("API_KEY") or os.getenv("EXCHANGE_API_KEY")
SECRET  = os.getenv("SECRET")  or os.getenv("EXCHANGE_SECRET_KEY")
MONGO_URL = os.getenv("MONGO_URL")
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1m")

if not API_KEY or not SECRET:
    logging.error("❌ API_KEY/SECRET تنظیم نشده.")
    time.sleep(10); raise SystemExit

db = MongoClient(MONGO_URL).get_database() if MONGO_URL else None
if db: logging.info(f"✅ Mongo متصل شد (trade).")
else:  logging.warning("⚠️ MONGO_URL نیست؛ ذخیره معاملات انجام نمی‌شود.")

ex = ExchangeAdapter.from_env()

def save_trade(trade):
    if db: db.trades.insert_one(trade); logging.info(f"💾 ثبت معامله: {trade}")

def main():
    logging.info(f"🚀 worker_trade برای {SYMBOL} شروع شد.")
    while True:
        try:
            # نمونه ساده: از signals بخوان
            sig = None
            if db: sig = db.signals.find_one(sort=[("ts",-1)])
            if not sig or int(time.time()) > int(sig.get("ttl",0)):
                time.sleep(2); continue
            side = sig["side"]
            if side not in {"buy","sell"}: time.sleep(2); continue

            t = ex.fetch_ticker(SYMBOL); px = float(t.get("last") or 0.0)
            if px <= 0: time.sleep(2); continue

            usd = float(os.getenv("USD_PER_TRADE","10"))
            amt = usd / max(px, 1e-9)
            order = ex.create_market_order(SYMBOL, side, amt)
            save_trade({"ts": int(time.time()*1000), "symbol": SYMBOL, "side": side,
                        "price": px, "amount": amt, "usd": usd, "raw": order})
            logging.info(f"✅ سفارش {side} @ {px} amount={amt}")
        except Exception as e:
            logging.error(f"trade error: {e}")
            traceback.print_exc()
        time.sleep(3)

if __name__ == "__main__":
    main()
