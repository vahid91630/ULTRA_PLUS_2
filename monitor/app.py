from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import os, socket

app = FastAPI(title="Ultra Monitor", docs_url=None, redoc_url=None)

def _has(k: str) -> bool:
    return bool(os.getenv(k))

# ---------- Root: HTML ساده تا مشکل encoding حل شود ----------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html lang="en"><meta charset="utf-8">
<title>Ultra Monitor</title>
<body style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; padding:18px;">
  <h2>Ultra Monitor</h2>
  <p>Links:</p>
  <ul>
    <li><a href="/status">/status</a></li>
    <li><a href="/status/full">/status/full</a></li>
    <li><a href="/debug/env">/debug/env</a></li>
  </ul>
</body>
</html>
"""

# ---------- /status: خلاصه ----------
@app.get("/status")
def status():
    need = ["API_KEY", "SECRET", "EXCHANGE", "SYMBOL", "TIMEFRAME"]
    miss = [k for k in need if not _has(k)]
    data = {
        "ok": len(miss) == 0,
        "missing_env": miss,
        "exchange": os.getenv("EXCHANGE", "mexc"),
        "sandbox": os.getenv("SANDBOX", "true"),
        "mongo_present": bool(os.getenv("MONGO_URL")),
        "host": socket.gethostname(),
    }
    return JSONResponse(content=data, media_type="application/json; charset=utf-8")

# ---------- /debug/env: برای بررسی سریع ----------
@app.get("/debug/env")
def debug_env():
    keep = ["API_KEY","SECRET","EXCHANGE","SANDBOX","SYMBOL","TIMEFRAME","MONGO_URL"]
    redacted = {"API_KEY","SECRET","MONGO_URL"}
    out = {}
    for k in keep:
        v = os.getenv(k)
        out[k] = ("***" if (k in redacted and v) else v)
    return JSONResponse(content=out, media_type="application/json; charset=utf-8")

# ---------- /status/full: تست Mongo + MEXC ----------
from pymongo import MongoClient
import ccxt
from urllib.parse import urlparse

@app.get("/status/full")
def status_full():
    result = {
        "app": "ok",
        "mongo": {"ok": False, "error": None, "db": None, "collections": []},
        "exchange": {"ok": False, "id": None, "auth": None, "error": None},
        "env_missing": [],
    }

    need = ["API_KEY","SECRET","EXCHANGE","SYMBOL","TIMEFRAME"]
    result["env_missing"] = [k for k in need if not _has(k)]

    # Mongo
    mongo_url = os.getenv("MONGO_URL")
    if mongo_url:
        try:
            client = MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
            dbname = urlparse(mongo_url).path.lstrip("/") or os.getenv("MONGO_DB") or "ULTRAplus"
            db = client.get_database(dbname)
            cols = db.list_collection_names()
            result["mongo"].update(ok=True, db=db.name, collections=cols)
        except Exception as e:
            result["mongo"]["error"] = str(e)
    else:
        result["mongo"]["error"] = "MONGO_URL not set"

    # Exchange (MEXC)
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
                "options": {"defaultType": "spot"},
            })
            ex.load_markets()
            result["exchange"]["id"] = ex.id
            # تست احراز هویت سبک
            ok_auth = False
            try:
                ex.check_required_credentials()
                _ = ex.fetch_balance()
                ok_auth = True
            except Exception as e:
                result["exchange"]["error"] = str(e)
            result["exchange"]["ok"] = True
            result["exchange"]["auth"] = "ok" if ok_auth else "failed"
        else:
            result["exchange"]["error"] = f"Exchange class not found: {name}"
    except Exception as e:
        result["exchange"]["error"] = str(e)

    return JSONResponse(content=result, media_type="application/json; charset=utf-8")
