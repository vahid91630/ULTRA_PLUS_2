from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from io.db import init_db, get_session, Heartbeat, Metric, Order, Fill, ErrorLog
from config.settings import SETTINGS
import datetime as dt
import socket

app = FastAPI(title="Ultra Dashboard", version="1.0", docs_url=None, redoc_url=None)

def _s()->Session: return get_session()

@app.on_event("startup")
def _startup(): init_db()

@app.get("/", response_class=HTMLResponse)
def root():
    # Fetch latest metrics, orders, fills, errors for dashboard summary
    s = _s()
    metrics = s.execute(select(Metric).order_by(desc(Metric.id)).limit(30)).scalars().all()
    orders = s.execute(select(Order).order_by(desc(Order.id)).limit(10)).scalars().all()
    fills = s.execute(select(Fill).order_by(desc(Fill.id)).limit(10)).scalars().all()
    errors = s.execute(select(ErrorLog).order_by(desc(ErrorLog.id)).limit(5)).scalars().all()
  equity_chart = ','.join(str(m.equity) for m in metrics[::-1])
  dd_chart = ','.join(str(m.drawdown) for m in metrics[::-1])
  ts_labels = ','.join(f'"{m.ts.strftime('%H:%M')}"' for m in metrics[::-1])
    return f"""
<!doctype html><meta charset='utf-8'>
<title>Ultra Dashboard</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,Arial;padding:16px;max-width:1100px;margin:auto;background:#f8f8ff}}
h1,h2{{margin:8px 0}} .grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}
.card{{border:1px solid #ddd;border-radius:10px;padding:12px;background:#fff;box-shadow:0 2px 8px #0001}}
a{{color:#6a4dff}}
.section{{margin-top:24px}}
.table{{width:100%;border-collapse:collapse}}
.table th,.table td{{border:1px solid #eee;padding:4px 8px;text-align:left}}
.chart-container{{width:100%;height:260px;margin-bottom:16px}}
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
<div class="section card">
  <h2>Equity & Drawdown (Last 30)</h2>
  <div class="chart-container">
    <canvas id="equityChart"></canvas>
  </div>
</div>
<div class="section card">
  <h2>Recent Orders</h2>
  <table class="table">
    <tr><th>ID</th><th>Time</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Price</th><th>Status</th><th>Paper</th></tr>
    {''.join(f'<tr><td>{o.id}</td><td>{o.ts.strftime('%Y-%m-%d %H:%M')}</td><td>{o.symbol}</td><td>{o.side}</td><td>{o.qty}</td><td>{o.price}</td><td>{o.status}</td><td>{o.paper}</td></tr>' for o in orders)}
  </table>
</div>
<div class="section card">
  <h2>Recent Fills</h2>
  <table class="table">
    <tr><th>ID</th><th>Time</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Price</th><th>Fee</th><th>Client</th></tr>
    {''.join(f'<tr><td>{f.id}</td><td>{f.ts.strftime('%Y-%m-%d %H:%M')}</td><td>{f.symbol}</td><td>{f.side}</td><td>{f.qty}</td><td>{f.price}</td><td>{f.fee}</td><td>{f.order_client_id}</td></tr>' for f in fills)}
  </table>
</div>
<div class="section card">
  <h2>Recent Errors</h2>
  <table class="table">
    <tr><th>Time</th><th>Where</th><th>Message</th></tr>
    {''.join(f'<tr><td>{e.ts.strftime('%Y-%m-%d %H:%M')}</td><td>{e.where}</td><td>{e.message}</td></tr>' for e in errors)}
  </table>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const ctx = document.getElementById('equityChart').getContext('2d');
new Chart(ctx, {
  type: 'line',
  data: {
    "labels": [{ts_labels}],
    "datasets": [
      {"label": 'Equity', "data": [{equity_chart}], "borderColor": '#6a4dff', "fill": false},
      {"label": 'Drawdown', "data": [{dd_chart}], "borderColor": '#ff4d4d', "fill": false}
    ]
  },
  options: {"responsive":true, "plugins": {"legend": {"display":true}}, "scales": {"y": {"beginAtZero":true}}}
});
</script>
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
