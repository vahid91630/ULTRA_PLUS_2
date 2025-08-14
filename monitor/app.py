from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os, socket

app = FastAPI(title="Ultra Monitor", docs_url=None, redoc_url=None)

def _has(k: str) -> bool: return bool(os.getenv(k))

@app.get("/status")
def status():
    need = ["API_KEY","SECRET","EXCHANGE","SYMBOL","TIMEFRAME"]
    miss = [k for k in need if not _has(k)]
    return JSONResponse({
        "ok": len(miss)==0,
        "missing_env": miss,
        "exchange": os.getenv("EXCHANGE","mexc"),
        "sandbox": os.getenv("SANDBOX","true"),
        "mongo_present": bool(os.getenv("MONGO_URL")),
        "host": socket.gethostname(),
    })

@app.get("/")
def home():
    return {"msg":"داشبورد آنلاین است. برای بررسی تنظیمات، /status و /debug/env را باز کن."}

@app.get("/debug/env")
def debug_env():
    keep = ["API_KEY","SECRET","EXCHANGE","SANDBOX","SYMBOL","TIMEFRAME","MONGO_URL"]
    redacted = {"API_KEY","SECRET","MONGO_URL"}
    out = {}
    for k in keep:
        v = os.getenv(k)
        out[k] = ("***" if (k in redacted and v) else v)
    return out
# ======= افزونه‌ی وضعیت کامل: Mongo + MEXC =======
from pymongo import MongoClient
import ccxt, time

@app.get("/status/full")
def status_full():
    result = {
        "app": "ok",
        "mongo": {"ok": False, "error": None, "db": None, "collections": []},
        "exchange": {"ok": False, "id": None, "auth": None, "error": None},
        "env_missing": [],
    }

    # بررسی ENVهای ضروری
    need = ["API_KEY","SECRET","EXCHANGE","SYMBOL","TIMEFRAME"]
    for k in need:
        if not os.getenv(k):
            result["env_missing"].append(k)

    # --- Mongo ---
    mongo_url = os.getenv("MONGO_URL")
    if mongo_url:
        try:
            client = MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
            # اگر DBName در URI نیست، اینجا از مسیر برداشت می‌کنیم یا ULTRAplus را استفاده می‌کنیم
            from urllib.parse import urlparse
            dbname = urlparse(mongo_url).path.lstrip("/") or os.getenv("MONGO_DB") or "ULTRAplus"
            db = client.get_database(dbname)
            db.list_collection_names()  # تست
            result["mongo"]["ok"] = True
            result["mongo"]["db"] = db.name
            result["mongo"]["collections"] = db.list_collection_names()
        except Exception as e:
            result["mongo"]["error"] = str(e)
    else:
        result["mongo"]["error"] = "MONGO_URL not set"

    # --- Exchange (MEXC) ---
    try:
        name = (os.getenv("EXCHANGE") or "mexc").lower()
        api  = os.getenv("EXCHANGE_API_KEY") or os.getenv("API_KEY") or ""
        sec  = os.getenv("EXCHANGE_SECRET_KEY") or os.getenv("SECRET") or ""
        ex_cls = getattr(ccxt, name, None) or getattr(ccxt, "mexc", None) or getattr(ccxt, "mexc3", None)
        if ex_cls:
            ex = ex_cls({
                "apiKey": api,
                "secret": sec,
                "enableRateLimit": True,
                "options": {"defaultType": "spot"}
            })
            # SANDBOX=false برای MEXC لازم است؛ اگر true باشد ممکن است متدها در دسترس نباشند
            if os.getenv("SANDBOX","false").lower() in {"1","true","yes","on"} and hasattr(ex, "set_sandbox_mode"):
                try: ex.set_sandbox_mode(True)
                except Exception: pass

            ex.load_markets()
            result["exchange"]["id"] = ex.id

            # تست احراز هویت سبک
            ok_auth = False
            try:
                ex.check_required_credentials()
                _ = ex.fetch_balance()  # اگر کلید غلط باشد، اینجا خطا می‌دهد
                ok_auth = True
            except Exception as e:
                result["exchange"]["error"] = str(e)

            result["exchange"]["ok"] = True
            result["exchange"]["auth"] = "ok" if ok_auth else "failed"
        else:
            result["exchange"]["error"] = f"Exchange class not found: {name}"
    except Exception as e:
        result["exchange"]["error"] = str(e)

    return JSONResponse(result)
