from __future__ import annotations
import json, time, sys
def jlog(level: str, msg: str, **kw):
    doc = {"ts": int(time.time()*1000), "level": level, "msg": msg}
    if kw: doc.update(kw)
    print(json.dumps(doc, ensure_ascii=False), flush=True, file=sys.stdout)
