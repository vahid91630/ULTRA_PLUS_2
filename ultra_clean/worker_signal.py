import os, time, logging
from datetime import datetime, timezone
from statistics import fmean
from pymongo import MongoClient
from ultra_clean.exchange import ExchangeAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1m")
MONGO_URL = os.getenv("MONGO_URL")
EMA_FAST = int(os.getenv("EMA_FAST", "12"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "26"))
TTL_SEC  = int(os.getenv("SIGNAL_TTL_SEC", "180"))

db = None
if MONGO_URL:
    db = MongoClient(MONGO_URL).get_database()
    logging.info("✅ Mongo متصل شد (signal).")
else:
    logging.warning("⚠️ MONGO_URL نیست؛ فقط لاگ می‌نویسم (signal).")

ex = ExchangeAdapter.from_env()
now_ms = lambda: int(datetime.now(timezone.utc).timestamp() * 1000)

def ema(vals, period):
    if len(vals) < period: return None
    k = 2/(period+1); e = fmean(vals[:period])
    for v in vals[period:]: e = v*k + e*(1-k)
    return e

def side_from_cross(fast, slow, fast_prev, slow_prev):
    if None in (fast, slow, fast_prev, slow_prev): return "hold"
    if fast_prev <= slow_prev and fast > slow: return "buy"
    if fast_prev >= slow_prev and fast < slow: return "sell"
    return "hold"

def main():
    logging.info(f"🚀 worker_signal برای {SYMBOL} tf={TIMEFRAME} شروع شد.")
    while True:
        try:
            ohlcv = ex.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=200) or []
            closes = [float(c[4]) for c in ohlcv][-100:]
            if len(closes) < max(EMA_FAST, EMA_SLOW)+1:
                logging.info("داده کافی نیست."); time.sleep(5); continue

            fast_prev = ema(closes[:-1], EMA_FAST)
            slow_prev = ema(closes[:-1], EMA_SLOW)
            fast_now  = ema(closes, EMA_FAST)
            slow_now  = ema(closes, EMA_SLOW)
            side = side_from_cross(fast_now, slow_now, fast_prev, slow_prev)
            score = 0.0
            if side == "buy":  score =  +abs((fast_now - slow_now)/slow_now)
            if side == "sell": score =  -abs((fast_now - slow_now)/slow_now)

            doc = {"ts": now_ms(), "symbol": SYMBOL, "tf": TIMEFRAME, "side": side,
                   "score": float(score), "ema_fast": float(fast_now or 0.0),
                   "ema_slow": float(slow_now or 0.0),
                   "ttl": int(time.time()) + TTL_SEC}
            if db: db.signals.insert_one(doc)
            logging.info(f"🔔 سیگنال: {side} score={score:.4f}")
        except Exception as e:
            logging.error(f"signal error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()
