#!/usr/bin/env python3
import os, time, subprocess, signal

RUN_TRADER = os.getenv("ENABLE_TRADER","true").lower() in {"1","true","yes","on"}
RUN_FUT = os.getenv("FUTURES","false").lower() in {"1","true","yes","on"}

COMMANDS = [
    ({"SERVICE_NAME":"web"}, ["uvicorn","monitor.app:app","--host","0.0.0.0","--port","8000"]),
    ({"SERVICE_NAME":"worker_ticker"}, ["python","-m","ultra_clean.worker_ticker"]),
    ({"SERVICE_NAME":"worker_equity"}, ["python","-m","ultra_clean.worker_equity"]),
]
if RUN_TRADER:
    COMMANDS += [
        ({"SERVICE_NAME":"worker_signal"}, ["python","-m","ultra_clean.worker_signal"]),
        ({"SERVICE_NAME":"worker_trade"}, ["python","-m","ultra_clean.worker_trade"]),
    ]

EXT_ORDER = [
    "activate_trading_system.py",
    "optimized_trading_system.py",
    "ultra_trading_system_with_new_apis.py",
    "daily_data_collection_system.py",
    "automated_news_monitoring_service.py",
    "telegram_bot_with_real_trading.py",
]
for fname in EXT_ORDER:
    path = os.path.join("ext", fname)
    if os.path.isfile(path):
        COMMANDS.append( ({"SERVICE_NAME":f"ext_{os.path.splitext(fname)[0]}"}, ["python", path]) )

PROCS=[]
def spawn(env_over, cmd):
    env = os.environ.copy(); env.update(env_over)
    print(f"[launcher] start: {env.get('SERVICE_NAME')} -> {' '.join(cmd)}", flush=True)
    return subprocess.Popen(cmd, env=env)

def stop_all(signum, frame):
    print("[launcher] stopping...", flush=True)
    for p in PROCS:
        try: p.terminate()
        except Exception: pass
    time.sleep(2)
    for p in PROCS:
        try:
            if p.poll() is None: p.kill()
        except Exception: pass
    raise SystemExit(0)

def main():
    signal.signal(signal.SIGINT, stop_all)
    signal.signal(signal.SIGTERM, stop_all)
    for env_over, cmd in COMMANDS:
        PROCS.append(spawn(env_over, cmd))
    while True:
        for i,p in enumerate(PROCS):
            ret = p.poll()
            if ret is not None:
                name = COMMANDS[i][0].get("SERVICE_NAME")
                print(f"[launcher] {name} exited code={ret} -> restart in 3s", flush=True)
                time.sleep(3)
                PROCS[i] = spawn(COMMANDS[i][0], COMMANDS[i][1])
        time.sleep(2)

if __name__ == "__main__":
    main()
