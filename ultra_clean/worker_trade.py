import os
import time
import logging
from pymongo import MongoClient
from ultra_clean.exchange import ExchangeAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

API_KEY = os.getenv("API_KEY")
SECRET  = os.getenv("SECRET")
MONGO_URL = os.getenv("MONGO_URL")
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1m")

if not API_KEY or not SECRET:
    logging.error("❌ API_KEY یا SECRET در Railway تنظیم نشده!")
    time.sleep(10)
    raise SystemExit

if not MONGO_URL:
    logging.warning("⚠️ MONGO_URL پیدا نشد. دیتاها در Mongo ذخیره نمی‌شوند.")
    mongo_db = None
else:
    client = MongoClient(MONGO_URL)
    mongo_db = client.get_database()
    logging.info(f"✅ اتصال به MongoDB برقرار شد: {mongo_db.name}")

ex = ExchangeAdapter.from_env()
logging.info(f"✅ اتصال به صرافی برقرار شد ({ex.ex.id})")

def save_trade(trade_data):
    if mongo_db:
        mongo_db.trades.insert_one(trade_data)
        logging.info(f"💾 ذخیره معامله در MongoDB: {trade_data}")
    else:
        logging.info(f"💾 [FAKE SAVE] {trade_data}")

def trade_loop():
    while True:
        try:
            ticker = ex.fetch_ticker(SYMBOL)
            price = ticker.get("last")
            logging.info(f"📊 قیمت فعلی {SYMBOL}: {price}")

            # نمونه استراتژی ساده
            if price and price < 60000:
                logging.info("🛒 خرید انجام شد!")
                order = ex.create_market_order(SYMBOL, "buy", 0.001)
                save_trade({"type": "buy", "price": price, "order": order})

            elif price and price > 70000:
                logging.info("💰 فروش انجام شد!")
                order = ex.create_market_order(SYMBOL, "sell", 0.001)
                save_trade({"type": "sell", "price": price, "order": order})

        except Exception as e:
            logging.error(f"⚠️ خطا در لوپ معامله: {e}")

        time.sleep(10)  # هر 10 ثانیه یکبار

if __name__ == "__main__":
    trade_loop()
