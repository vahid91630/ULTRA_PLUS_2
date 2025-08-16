from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from io_mod.db import init_db, get_session, Heartbeat, Metric, Order, Fill, ErrorLog
from config.settings import SETTINGS
import datetime as dt
import socket

app = FastAPI(title="Ultra Dashboard", version="1.0", docs_url=None, redoc_url=None)

def _s()->Session: return get_session()

@app.on_event("startup")
def _startup(): init_db()

@app.get("/", response_class=HTMLResponse)
def root():
  # --- نمایش موجودی واقعی صرافی (MEXC) با ccxt ---
  balance_html = "<div class='section card' style='background:#e3f2fd;'><h2>موجودی صرافی</h2>"
  try:
    import ccxt
    api_key = getattr(SETTINGS, 'api_key', None) or getattr(SETTINGS, 'API_KEY', None) or ''
    secret = getattr(SETTINGS, 'secret_key', None) or getattr(SETTINGS, 'SECRET', None) or ''
    if api_key and secret:
      ex = ccxt.mexc({"apiKey": api_key, "secret": secret, "enableRateLimit": True})
      bal = ex.fetch_balance()
      balance_html += "<table class='table'><tr><th>ارز</th><th>مقدار</th></tr>"
      for coin, v in bal['total'].items():
        if v:
          balance_html += f"<tr><td>{coin}</td><td>{v}</td></tr>"
      balance_html += "</table>"
    else:
      balance_html += "<div style='color:#b71c1c'>کلید API یا Secret تنظیم نشده است.</div>"
  except Exception as e:
    balance_html += f"<div style='color:#b71c1c'>خطا در دریافت موجودی: {str(e)}</div>"
  balance_html += "</div>"
  import json
  from pathlib import Path
  # Load API keys status
  api_keys_status = {}
  try:
    with open(Path(__file__).parent.parent / "ext" / "api_keys_status.json", encoding="utf-8") as f:
      api_keys_status = json.load(f)
  except Exception:
    api_keys_status = None
  # Load learning progress
  learning_progress = {}
  try:
    with open(Path(__file__).parent.parent / "ext" / "learning_progress.json", encoding="utf-8") as f:
      learning_progress = json.load(f)
  except Exception:
    learning_progress = None
  # Load AI intelligence report
  ai_intel = {}
  try:
    with open(Path(__file__).parent.parent / "ext" / "ai_intelligence_report.json", encoding="utf-8") as f:
      ai_intel = json.load(f)
  except Exception:
    ai_intel = None

  # Fetch latest metrics, orders, fills, errors for dashboard summary
  s = _s()
  metrics = s.execute(select(Metric).order_by(desc(Metric.id)).limit(30)).scalars().all()
  orders = s.execute(select(Order).order_by(desc(Order.id)).limit(10)).scalars().all()
  fills = s.execute(select(Fill).order_by(desc(Fill.id)).limit(10)).scalars().all()
  errors = s.execute(select(ErrorLog).order_by(desc(ErrorLog.id)).limit(5)).scalars().all()
  # Prepare HTML table rows and JS arrays outside the f-string to avoid nested expressions
  order_rows = "".join([
    f"<tr><td>{o.id}</td><td>{o.ts.strftime('%Y-%m-%d %H:%M')}</td><td>{o.symbol}</td><td>{o.side}</td><td>{o.qty}</td><td>{o.price}</td><td>{o.status}</td><td>{o.paper}</td></tr>"
    for o in orders
  ])
  fill_rows = "".join([
    f"<tr><td>{f.id}</td><td>{f.ts.strftime('%Y-%m-%d %H:%M')}</td><td>{f.symbol}</td><td>{f.side}</td><td>{f.qty}</td><td>{f.price}</td><td>{f.fee}</td><td>{f.order_client_id}</td></tr>"
    for f in fills
  ])
  error_rows = "".join([
    f"<tr><td>{e.ts.strftime('%Y-%m-%d %H:%M')}</td><td>{e.where}</td><td>{e.message}</td></tr>"
    for e in errors
  ])
  equity_chart = [m.equity for m in metrics[::-1]]
  dd_chart = [m.drawdown for m in metrics[::-1]]
  ts_labels = [m.ts.strftime('%H:%M') for m in metrics[::-1]]

  # فارسی‌سازی و بهبود گرافیکی
  api_keys_html = "<div class='section card'><h2>وضعیت کلیدهای API</h2>"
  if api_keys_status and "api_keys" in api_keys_status:
    api_keys_html += "<table class='table'><tr><th>نام</th><th>توضیح</th><th>وضعیت</th><th>کاربرد</th></tr>"
    for k, v in api_keys_status["api_keys"].items():
      api_keys_html += f"<tr><td>{v.get('name',k)}</td><td>{v.get('description','')}</td><td>{v.get('status','')}</td><td>{v.get('usage','')}</td></tr>"
    api_keys_html += "</table>"
    api_keys_html += f"<div><b>توصیه‌ها:</b> {'؛ '.join(api_keys_status.get('recommendations', []))}</div>"
  else:
    api_keys_html += "<div>داده‌ای برای وضعیت کلیدها موجود نیست.</div>"
  api_keys_html += "</div>"

  learning_html = "<div class='section card'><h2>پیشرفت یادگیری سیستم</h2>"
  if learning_progress:
    learning_html += f"<div>سطح هوش: {learning_progress.get('intelligence_level','')}</div>"
    learning_html += f"<div>الگوهای یادگرفته‌شده: {learning_progress.get('patterns_learned','')}</div>"
    learning_html += f"<div>دقت پیش‌بینی: {learning_progress.get('prediction_accuracy','')}</div>"
    learning_html += f"<div>چرخه‌های یادگیری: {learning_progress.get('learning_cycles','')}</div>"
    learning_html += f"<div>درصد برد: {learning_progress.get('win_rate','')}</div>"
    learning_html += f"<div>ساعت یادگیری: {learning_progress.get('learning_hours','')}</div>"
    learning_html += f"<div>یادگیری پیشرفته: {learning_progress.get('enhanced_learning_enabled','')}</div>"
    learning_html += f"<div>آخرین بروزرسانی: {learning_progress.get('last_update','')}</div>"
  else:
    learning_html += "<div>داده‌ای برای پیشرفت یادگیری موجود نیست.</div>"
  learning_html += "</div>"

  ai_html = "<div class='section card'><h2>گزارش هوش مصنوعی</h2>"
  if ai_intel and "current_intelligence" in ai_intel:
    ci = ai_intel["current_intelligence"]
    ai_html += f"<div>سطح: {ci.get('level','')}</div>"
    ai_html += f"<div>هوش فعال: {', '.join(ci.get('active_ai',[]))}</div>"
    ai_html += f"<div>پتانسیل: {ci.get('potential','')}</div>"
    ai_html += f"<div>آخرین بروزرسانی: {ai_intel.get('timestamp','')}</div>"
  else:
    ai_html += "<div>داده‌ای برای هوش مصنوعی موجود نیست.</div>"
  ai_html += "</div>"


  # گزارش آنلاین (نمونه)
  live_report_html = "<div class='section card' style='background:#fffde7;'><h2>گزارش آنلاین</h2>"
  live_report_html += "<div>سیستم فعال است و داده‌ها هر دقیقه بروزرسانی می‌شوند.</div>"
  live_report_html += "</div>"

  return f"""
<!doctype html><meta charset='utf-8'>
<title>داشبرد هوشمند Bardziel</title>
<style>
body{font-family:'Vazirmatn',Tahoma,Arial,sans-serif;direction:rtl;padding:16px;max-width:1200px;margin:auto;background:#f8f8ff}
h1,h2{margin:8px 0;text-align:right} .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.card{border:1px solid #90caf9;border-radius:10px;padding:16px;background:#fff;box-shadow:0 2px 8px #2196f31a}
a{color:#1976d2}
.section{margin-top:24px}
.table{width:100%;border-collapse:collapse;background:#fff}
.table th,.table td{border:1px solid #bbdefb;padding:6px 12px;text-align:right;font-size:15px}
.chart-container{width:100%;height:260px;margin-bottom:16px}
@import url('https://cdn.fontcdn.ir/Font/Persian/Vazirmatn/Vazirmatn.css');
</style>
<h1>داشبرد هوشمند Bardziel</h1>
<p>سرور: <b>{socket.gethostname()}</b></p>
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
  <h2>سرمایه و افت سرمایه (۳۰ مقدار آخر)</h2>
  <div class="chart-container">
    <canvas id="equityChart"></canvas>
  </div>
</div>
{balance_html}
{api_keys_html}
{learning_html}
{ai_html}
{live_report_html}
<div class="section card">
  <h2>سفارش‌های اخیر</h2>
  <table class="table">
    <tr><th>کد</th><th>زمان</th><th>نماد</th><th>سمت</th><th>مقدار</th><th>قیمت</th><th>وضعیت</th><th>آزمایشی</th></tr>
    {order_rows}
  </table>
</div>
<div class="section card">
  <h2>معاملات انجام‌شده</h2>
  <table class="table">
    <tr><th>کد</th><th>زمان</th><th>نماد</th><th>سمت</th><th>مقدار</th><th>قیمت</th><th>کارمزد</th><th>شناسه سفارش</th></tr>
    {fill_rows}
  </table>
</div>
<div class="section card">
  <h2>خطاهای اخیر</h2>
  <table class="table">
    <tr><th>زمان</th><th>ماژول</th><th>پیام خطا</th></tr>
    {error_rows}
  </table>
</div>
<script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
<script>
const ctx = document.getElementById('equityChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {ts_labels},
    datasets: [
      {{label: 'Equity', data: {equity_chart}, borderColor: '#6a4dff', fill: false}},
      {{label: 'Drawdown', data: {dd_chart}, borderColor: '#ff4d4d', fill: false}}
    ]
  }},
  options: {{responsive:true, plugins: {{legend: {{display:true}}}}, scales: {{y: {{beginAtZero:true}}}}}}
}});
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
