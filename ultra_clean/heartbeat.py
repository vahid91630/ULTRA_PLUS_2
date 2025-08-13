from __future__ import annotations
import time
from typing import Any, Dict
from .config import AppConfig
from .db import DB
def beat(cfg: AppConfig, db: DB, status: str="ok", **fields: Any) -> None:
    now = int(time.time()*1000)
    doc: Dict[str, Any] = {"service": cfg.service_name, "ts": now, "status": status, "ver": cfg.app_ver}
    if fields: doc.update(fields)
    db.heartbeats.update_one({"service": cfg.service_name}, {"$set": doc}, upsert=True)
