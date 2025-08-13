from __future__ import annotations
import os, time
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL")
APP_VER = os.getenv("APP_VER","v1")
HB_WARN = int(os.getenv("HB_WARN_SEC","30"))
HB_DEAD = int(os.getenv("HB_DEAD_SEC","120"))

app = FastAPI(title="Ultra Dashboard", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__),"assets")), name="static")

_db = None

@app.on_event("startup")
async def _startup():
    global _db
    if not MONGO_URL:
        raise RuntimeError("MONGO_URL is required")
    cli = AsyncIOMotorClient(MONGO_URL)
    _db = cli["ultra"]

@app.get("/status")
async def status():
    return {"ok": True, "ver": APP_VER, "ts": int(time.time()*1000)}

@app.get("/services")
async def services() -> List[Dict[str,Any]]:
    assert _db
    now = int(time.time()*1000)
    out=[]
    async for h in _db["heartbeats"].find({}):
        age = (now - int(h.get("ts",0)))//1000
        if age >= HB_DEAD: state="dead"
        elif age >= HB_WARN: state="warn"
        else: state="ok"
        info = {k:v for k,v in h.items() if k not in {"_id","service","ts","status","ver"}}
        out.append({"service": h.get("service"), "state": state, "ago_sec": int(age), "status": h.get("status","ok"), "ver": h.get("ver",APP_VER), "info": info})
    return out

@app.get("/kpi")
async def kpi():
    assert _db
    raw = await _db["raw_events"].estimated_document_count()
    scored = await _db["scored_events"].estimated_document_count()
    signals = await _db["signals"].estimated_document_count()
    last_eq = await _db["equity"].find_one(sort=[("ts",-1)])
    return {"raw_events": raw, "scored_events": scored, "signals_count": signals, "last_equity": (last_eq or {}).get("equity")}

@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""<!doctype html><html lang='fa' dir='rtl'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/>
<title>داشبورد اولترا</title><style>
body{{font-family:sans-serif;margin:16px;background:#fafafa}} .card{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px;margin-bottom:12px}}
.state-ok{{color:#137333}} .state-warn{{color:#b26a00}} .state-dead{{color:#b00020}} table{{width:100%;border-collapse:collapse}} td,th{{border-bottom:1px solid #eee;padding:6px}}
</style></head><body>
<h2>داشبورد اولترا <small>{APP_VER}</small></h2>
<div class='card'><h3>سلامت</h3><pre id='st'>...</pre></div>
<div class='card'><h3>وضعیت سرویس‌ها</h3><table><thead><tr><th>سرویس</th><th>وضعیت</th><th>آخرین هماهنگی</th><th>جزئیات</th></tr></thead><tbody id='tb'></tbody></table></div>
<div class='card'><h3>KPI</h3><pre id='kpi'>...</pre></div>
<script>
async function load(){{
    const s=await fetch('/status').then(r=>r.json()); document.getElementById('st').textContent=JSON.stringify(s,null,2);
    const k=await fetch('/kpi').then(r=>r.json()); document.getElementById('kpi').textContent=JSON.stringify(k,null,2);
    const sv=await fetch('/services').then(r=>r.json());
    const tb=document.getElementById('tb'); tb.innerHTML='';
    sv.forEach(x=>{{
        const cls = x.state==='ok'?'state-ok':(x.state==='warn'?'state-warn':'state-dead');
        const tr=document.createElement('tr');
        tr.innerHTML=`<td>${{x.service}}</td><td class='${{cls}}'>${{x.state}}</td><td>${{x.ago_sec}}s</td><td><code>${{JSON.stringify(x.info||{})}}</code></td>`;
        tb.appendChild(tr);
    }});
}}
load(); setInterval(load, 5000);
</script>
</body></html>"""
