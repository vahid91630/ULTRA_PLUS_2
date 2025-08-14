from __future__ import annotations
import time, uuid
import ccxt
from typing import Optional, Tuple
from config.settings import SETTINGS

class CircuitBreaker:
    def __init__(self, fail_threshold:int=5, cool_sec:int=30):
        self.fail_threshold=fail_threshold; self.cool_sec=cool_sec
        self.fails=0; self.open_until=0.0
    def ok(self): return time.time() >= self.open_until
    def mark_success(self): self.fails=0
    def mark_fail(self):
        self.fails+=1
        if self.fails>=self.fail_threshold:
            self.open_until=time.time()+self.cool_sec
            self.fails=0

def _bps(x: float) -> float: return x/10000.0
def _slip(price: float, bps: float, side: str) -> float:
    return price * (1 + (_bps(bps) if side=="buy" else -_bps(bps)))

class PaperBroker:
    def __init__(self, fee_bps: float, slippage_bps: float):
        self.fee_bps=fee_bps; self.slippage_bps=slippage_bps
        self.cash=10_000.0; self.pos_qty=0.0; self.avg_price=0.0
    def create_market_order(self, symbol:str, side:str, qty:float, last_price:float):
        price=_slip(last_price, self.slippage_bps, side)
        fee = abs(qty*price) * _bps(self.fee_bps)
        if side=="buy":
            cost=qty*price+fee
            if cost>self.cash: raise RuntimeError("insufficient cash (paper)")
            self.cash -= cost
            self.avg_price = (self.avg_price*self.pos_qty + qty*price)/ (self.pos_qty+qty) if self.pos_qty+qty>0 else price
            self.pos_qty += qty
        else:
            proceeds=qty*price - fee
            if qty>self.pos_qty: raise RuntimeError("insufficient position (paper)")
            self.cash += proceeds
            self.pos_qty -= qty
            if self.pos_qty==0: self.avg_price=0.0
        order={"status":"filled","price":price,"qty":qty,"side":side,"symbol":symbol}
        fill={"price":price,"qty":qty,"fee":fee,"side":side,"symbol":symbol}
        return order, fill

class MexcExchange:
    def __init__(self, api_key:str, api_secret:str):
        name=(SETTINGS.exchange or "MEXC").lower()
        cls = getattr(ccxt, name, None) or getattr(ccxt, "mexc", None) or getattr(ccxt, "mexc3", None)
        self.breaker = CircuitBreaker()
        self.ex = cls({
            "apiKey": api_key, "secret": api_secret,
            "enableRateLimit": True, "options": {"defaultType":"spot"},
        })
        self.ex.load_markets()
    def fetch_ticker(self, symbol:str)->dict:
        for attempt in range(5):
            if not self.breaker.ok(): raise RuntimeError("circuit open")
            try:
                t=self.ex.fetch_ticker(symbol); self.breaker.mark_success(); return t
            except Exception:
                self.breaker.mark_fail(); time.sleep(0.5*(attempt+1))
        raise RuntimeError("ticker failed")
    def create_market_order(self, symbol:str, side:str, qty:float, client_id:str)->dict:
        for attempt in range(5):
            if not self.breaker.ok(): raise RuntimeError("circuit open")
            try:
                o=self.ex.create_order(symbol, "market", side, qty, params={"clientOrderId": client_id})
                self.breaker.mark_success(); return o
            except Exception:
                self.breaker.mark_fail(); time.sleep(0.5*(attempt+1))
        raise RuntimeError("order failed")

def make_broker(): return PaperBroker(SETTINGS.fee_bps, SETTINGS.slippage_bps)
def make_exchange_if_available()->Optional[MexcExchange]:
    if not (SETTINGS.api_key and SETTINGS.api_secret): return None
    try: return MexcExchange(SETTINGS.api_key, SETTINGS.api_secret)
    except Exception: return None
def make_client_pair():
    return make_exchange_if_available(), make_broker()
def gen_client_order_id(tag:str)->str:
    return f"{tag}-" + uuid.uuid4().hex[:16]
