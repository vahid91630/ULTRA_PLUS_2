from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os, socket

app = FastAPI(title="Ultra Monitor", docs_url=None, redoc_url=None)

def _has(k: str) -> bool: return bool(os.getenv(k))

@app.get("/status")
def status():
    need = ["API_KEY","SECRET","EXCHANGE","SYMBOL","TIMEFRAME"]
    miss = [k for k in need if not _has(k)]
    mongo = os.getenv("MONGO_URL")
    return JSONResponse({
        "ok": len(miss)==0,
        "missing_env": miss,
        "exchange": os.getenv("EXCHANGE","mexc"),
        "sandbox": os.getenv("SANDBOX","true"),
        "mongo_present": bool(mongo),
        "host": socket.gethostname(),
    })

@app.get("/")
def home():
    return {"msg":"داشبورد آنلاین است. /status را باز کن برای وضعیت."}

@app.get("/debug/env")
def debug_env():
    keep = ["API_KEY","SECRET","EXCHANGE","SANDBOX","SYMBOL","TIMEFRAME","MONGO_URL"]
    return {k: ("***" if k in {"API_KEY","SECRET","MONGO_URL"} and _has(k) else os.getenv(k)) for k in keep}
