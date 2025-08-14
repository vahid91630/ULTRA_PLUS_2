from __future__ annotations
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from io.db import init_db, get_session, Heartbeat, Metric, Order, Fill, ErrorLog
from config.settings import SETTINGS
import datetime as dt, socket

app = FastAPI(title="Ultra Dashboard", version="1.0", docs_url=None, redoc_url=None)

def _s()->Session: return get_session()

@app.on_event("startup")
def _startup(): init_db()

@app.get("/", response_class=HTMLResponse)
def root():
    return f"""<!doctype html><meta charset="utf-8">
<title>Ultra Dashboard</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,Arial;padding:16px;max-width:900px;margin:auto}}
h1,h2{{margin:8px 0}} .grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}
.card{{border:1px solid #ddd;border-radius:10px;padding:12px}} a{{color:#6a4dff}}
</style>
<h1>Ultra Dashboard</h1>
<p>Server: <b>{socket.gethostname()}</b></p>
<div class="grid">
  <div class="card"><h3>Links</h3>
    <ul>
      <li><a href="/healthz">/healthz</a></li>
      <li><a href="/readyz">/readyz</a></li>
      <li><a href="/status">/status</a></li>
      <li><a href="/metrics">/metrics</a></li>
      <li><a href="/orders">/orders</a></li>
      <li><a href="/fills">/fills</a></li>
      <li><a href="/errors">/errors</a></li>
    </ul>
  </div>
  <div class="card"><h3>ENV</h3>
    <div>MODE: {SETTINGS.mode}</div>
    <div>EXCHANGE: {SETTINGS.exchange}</div>
    <div>SYMBOL: {SETTINGS.symbol}</div>
    <div>TIMEFRAME: {SETTINGS.timeframe}</div>
  </div>
</div>
"""

@app.get("/healthz")
def healthz():
    return {"status":"ok","mode":SETTINGS.mode,"exchange":SETTINGS.exchange,"timestamp":dt.datetime.utcnow().isoformat()+"Z"}

@app.get("/readyz")
def readyz():
    s=_s()
    hb = s.execute(select(Heartbeat).order_by(desc(Heartbeat.ts)).limit(1)).scalars().first()
    ready = hb is not None
    return {"ready": ready, "last_heartbeat": (hb.ts.isoformat()+"Z" if hb else None)}

@app.get("/status")
def status():
    s=_s()
    m = s.execute(select(Metric).order_by(desc(Metric.id)).limit(1)).scalars().first()
    return {"mode": SETTINGS.mode, "symbol": SETTINGS.symbol,
            "equity": (m.equity if m else None), "drawdown": (m.drawdown if m else None)}

@app.get("/metrics")
def metrics():
    s=_s()
    rows = s.execute(select(Metric).order_by(desc(Metric.id)).limit(200)).scalars().all()
    return {"count": len(rows), "items": [{"ts": r.ts.isoformat()+"Z", "equity": r.equity, "dd": r.drawdown} for r in rows]}

@app.get("/orders")
def orders():
    s=_s()
    rows = s.execute(select(Order).order_by(desc(Order.id)).limit(100)).scalars().all()
    return {"count": len(rows), "items": [
        {"id": r.id, "ts": r.ts.isoformat()+"Z", "symbol": r.symbol, "side": r.side,
         "qty": r.qty, "price": r.price, "status": r.status, "paper": r.paper}
    for r in rows]}

@app.get("/fills")
def fills():
    s=_s()
    rows = s.execute(select(Fill).order_by(desc(Fill.id)).limit(100)).scalars().all()
    return {"count": len(rows), "items": [
        {"id": r.id, "ts": r.ts.isoformat()+"Z", "symbol": r.symbol, "side": r.side,
         "qty": r.qty, "price": r.price, "fee": r.fee, "client": r.order_client_id}
    for r in rows]}

@app.get("/errors")
def errors():
    s=_s()
    rows = s.execute(select(ErrorLog).order_by(desc(ErrorLog.id)).limit(100)).scalars().all()
    return {"count": len(rows), "items": [{"ts": r.ts.isoformat()+"Z", "where": r.where, "message": r.message} for r in rows]}
