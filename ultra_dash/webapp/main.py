# -*- coding: utf-8 -*-
"""
داشبورد فارسی Ultra – FastAPI
- مسیر اصلی: / (UI)
- API سلامت: /api/status
- هلث‌چک‌ها: /healthz , /readyz
- نسخه‌ی متنی: /status , /status/full , /debug/env
"""
import os, socket, json
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

try:
    import pymongo
    from pymongo import MongoClient
except Exception:
    pymongo = None
    MongoClient = None

try:
    import ccxt
except Exception:
    ccxt = None

APP_NAME = os.getenv("APP_NAME", "Ultra Monitor")
EXCHANGE = os.getenv("EXCHANGE", "mexc").lower()
API_KEY = os.getenv("API_KEY") or os.getenv("MEXC_API_KEY") or os.getenv("EXCHANGE_API_KEY")
SECRET  = os.getenv("SECRET")  or os.getenv("MEXC_API_SECRET") or os.getenv("EXCHANGE_API_SECRET")
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1m")
MONGO_URL = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL")
SANDBOX = os.getenv("SANDBOX")
if SANDBOX is not None:
    SANDBOX = str(SANDBOX).strip().lower() in {"1","true","yes","on"}

app = FastAPI(title=APP_NAME, docs_url=None, redoc_url=None)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

def check_mongo() -> Dict[str, Any]:
    if not MONGO_URL:
        return {"ok": False, "error": "MONGO_URL خالی است"}
    if not pymongo or not MongoClient:
        return {"ok": False, "error": "pymongo نصب نیست"}
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=2500)
        client.admin.command("ping")
        dbname = (client.get_default_database().name
                  if client.get_default_database() is not None else "ULTRAplus")
        db = client[dbname]
        cols = db.list_collection_names()
        return {"ok": True, "db": dbname, "collections": cols}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def check_exchange() -> Dict[str, Any]:
    if EXCHANGE != "mexc":
        return {"ok": False, "error": "فقط mexc فعال است در این داشبورد"}
    if ccxt is None:
        return {"ok": False, "error": "ccxt نصب نیست"}
    try:
        ex = ccxt.mexc({
            "apiKey": API_KEY or "",
            "secret": SECRET or "",
            "enableRateLimit": True,
        })
        ex.load_markets()
        err = None
        if API_KEY and SECRET:
            try:
                ex.fetch_balance({"recvWindow": 10000})
                auth = True
            except Exception as ee:
                err = str(ee)
                auth = False
        else:
            auth = None
        return {"ok": True, "id": ex.id, "auth": auth, "error": err}
    except Exception as e:
        return {"ok": False, "id": None, "auth": None, "error": str(e)}

def current_env_min() -> Dict[str, Any]:
    return {
        "API_KEY": "***" if API_KEY else "",
        "SECRET": "***" if SECRET else "",
        "EXCHANGE": EXCHANGE,
        "SANDBOX": SANDBOX,
        "SYMBOL": SYMBOL,
        "TIMEFRAME": TIMEFRAME,
        "MONGO_URL": "***" if MONGO_URL else "",
    }

def status_payload(full: bool = False) -> Dict[str, Any]:
    env_missing = []
    for k in ["EXCHANGE", "SYMBOL", "TIMEFRAME"]:
        if not globals().get(k):
            env_missing.append(k)
    info = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "host": socket.gethostname()[:12],
        "app": "ok",
        "env_missing": env_missing,
        "exchange": EXCHANGE,
        "sandbox": "true" if SANDBOX else "false",
        "mongo_present": True if MONGO_URL else False,
    }
    if full:
        info["env"] = current_env_min()
        info["mongo"] = check_mongo()
        info["exchange_status"] = check_exchange()
    return info

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": APP_NAME,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
    })

@app.get("/api/status")
async def api_status():
    return JSONResponse(status_payload(full=True))

@app.get("/status", response_class=PlainTextResponse)
async def status_text():
    return PlainTextResponse(json.dumps(status_payload(False), ensure_ascii=False))

@app.get("/status/full", response_class=PlainTextResponse)
async def status_full_text():
    return PlainTextResponse(json.dumps(status_payload(True), ensure_ascii=False))

@app.get("/debug/env", response_class=PlainTextResponse)
async def debug_env():
    return PlainTextResponse(json.dumps(current_env_min(), ensure_ascii=False))

@app.get("/healthz")
async def healthz():
    return JSONResponse({"ok": True})

@app.get("/readyz")
async def readyz():
    mg = check_mongo() if MONGO_URL else {"ok": True}
    cx = check_exchange()
    ok = mg.get("ok", False) and cx.get("ok", False)
    return JSONResponse({"ok": ok, "mongo": mg.get("ok"), "exchange": cx.get("ok")})
