from __future__ import annotations
import argparse, time
from sqlalchemy.orm import Session
from config.settings import SETTINGS
from io.db import init_db, get_session, record_heartbeat, record_error, Order, Fill, Metric
from exchange_mexc import make_client_pair, gen_client_order_id
from core.strategy import EmaCross
from core.portfolio import Portfolio

def _cap_usd(eq: float) -> float:
    return min(max(10.0, eq * SETTINGS.risk_per_trade), SETTINGS.max_usd_per_trade)
def _qty_from_usd(usd: float, price: float) -> float:
    return round(max(0.0, usd / max(price, 1e-6)), 6)
def _bps(x: float) -> float: return x / 10000.0

def run(mode: str):
    init_db()
    strategy = EmaCross()
    ex, paper = make_client_pair()
    sess: Session = get_session()
    port = Portfolio()
    last_peak_equity = 0.0

    symbol = SETTINGS.symbol
    heartbeat_int = max(SETTINGS.heartbeat_sec, 5)
    last_hb = 0.0
    live = (mode.lower() == "live" and ex is not None)

    open_qty, avg_price, sl_price, tp_price = 0.0, 0.0, None, None

    while True:
        try:
            t = ex.fetch_ticker(symbol) if ex else __import__("ccxt").binance().fetch_ticker(symbol)
            price = float(t.get("last") or t.get("close") or 0.0)
            if not price: time.sleep(SETTINGS.heartbeat_sec); continue

            strategy.push(price)
            sig = strategy.signal()

            if time.time() - last_hb > heartbeat_int:
                record_heartbeat(sess, component=("engine_live" if live else "engine_paper"))
                last_hb = time.time()

            equity_now = port.equity(price)
            last_peak_equity = max(last_peak_equity, equity_now)
            usd = _cap_usd(equity_now)
            qty = _qty_from_usd(usd, price)

            if abs(open_qty) * price >= SETTINGS.max_position_usd:
                sig = "hold"

            if open_qty > 0:
                if sl_price and price <= sl_price: sig = "sell"
                if tp_price and price >= tp_price: sig = "sell"

            if sig in ("buy", "sell") and qty > 0:
                side = sig
                client_id = gen_client_order_id("live" if live else "paper")
                if live:
                    o = ex.create_market_order(symbol, side, qty, client_id)
                    f_price = float(o.get("average") or o.get("price") or price)
                    f_fee = abs(qty * f_price) * _bps(SETTINGS.fee_bps)
                else:
                    o, f = paper.create_market_order(symbol, side, qty, price)
                    f_price = f["price"]; f_fee = f["fee"]

                oid = int(time.time() * 1e6) % 2_147_483_647
                sess.add(Order(id=oid, client_id=client_id, symbol=symbol, side=side,
                               qty=qty, price=f_price, status="filled", paper=not live))
                sess.add(Fill(order_client_id=client_id, symbol=symbol, side=side,
                              qty=qty, price=f_price, fee=f_fee))
                sess.commit()

                port.update_fill(side, qty, f_price, f_fee)

                if side == "buy":
                    avg_price = (avg_price * open_qty + f_price * qty) / (open_qty + qty) if open_qty else f_price
                    open_qty += qty
                    sl_price = avg_price * (1.0 - _bps(SETTINGS.stop_loss_bps))
                    tp_price = avg_price * (1.0 + _bps(SETTINGS.take_profit_bps))
                else:
                    open_qty = max(0.0, open_qty - qty)
                    if open_qty == 0:
                        avg_price, sl_price, tp_price = 0.0, None, None

            eq = port.equity(price)
            dd = 0.0 if last_peak_equity == 0 else max(0.0, (last_peak_equity - eq) / last_peak_equity)
            sess.add(Metric(equity=eq, drawdown=dd, turnover=abs(qty * price))); sess.commit()

            time.sleep(2)

        except Exception as e:
            record_error(sess, "engine", str(e))
            time.sleep(2)

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default=SETTINGS.mode)
    args = p.parse_args()
    run(mode=args.mode)

if __name__ == "__main__":
    main()
