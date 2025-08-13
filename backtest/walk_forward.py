from __future__ import annotations
import ccxt, time, json
from statistics import mean
def sma(vals,n):
    return [ (mean(vals[i-n+1:i+1]) if i>=n-1 else None) for i in range(len(vals)) ]
def run(exchange="mexc", symbol="BTC/USDT", timeframe="1m", fast=9, slow=21, limit=3000):
    ex = getattr(ccxt, exchange)({"enableRateLimit": True})
    data = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    closes = [x[4] for x in data]
    f = sma(closes, fast); s = sma(closes, slow)
    pos=0; entry=0.0; pnl=0.0; wins=0; losses=0
    for i in range(1,len(closes)):
        if f[i-1] and s[i-1]:
            if f[i-1] <= s[i-1] and f[i] and s[i] and f[i] > s[i] and pos==0:
                entry = closes[i]; pos=1
            elif f[i-1] >= s[i-1] and f[i] and s[i] and f[i] < s[i] and pos==1:
                diff = closes[i]-entry; pnl += diff; wins += 1 if diff>0 else 0; losses += 0 if diff>0 else 1; pos=0
    ret = pnl / closes[0] if closes else 0.0
    return {"ret": ret, "wins": wins, "losses": losses, "ts": int(time.time()*1000)}
if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
