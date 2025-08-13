#!/usr/bin/env python3
import os, sys, time, subprocess, signal, shutil

RUN_FUTURES = os.getenv("FUTURES","false").lower() in {"1","true","yes","on"}
HAS_MONGO   = bool(os.getenv("MONGO_URL"))
PY = shutil.which("python") or "python"

COMMANDS = [
    ({"SERVICE_NAME":"web"}, ["uvicorn","monitor.app:app","--host","0.0.0.0","--port","8000"]),
]

if HAS_MONGO:
    COMMANDS += [
        ({"SERVICE_NAME":"worker_ticker"}, [PY,"-m","ultra_clean.worker_ticker"]),
        ({"SERVICE_NAME":"worker_signal"}, [PY,"-m","ultra_clean.worker_signal"]),
        ({"SERVICE_NAME":"worker_trade"},  [PY,"-m","ultra_clean.worker_trade"]),
        ({"SERVICE_NAME":"worker_equity"}, [PY,"-m","ultra_clean.worker_equity"]),
    ]
    if RUN_FUTURES:
        COMMANDS += [
            ({"SERVICE_NAME":"worker_trade_futures"},  [PY,"-m","ultra_clean.worker_trade_futures"]),
            ({"SERVICE_NAME":"worker_equity_futures"}, [PY,"-m","ultra_clean.worker_equity_futures"]),
        ]

EXTS = [
    ("ext_activate", [PY,"ext/activate_trading_system.py"]),
    ("ext_news",     [PY,"ext/automated_news_monitoring_service.py"]),
    ("ext_telegram", [PY,"ext/telegram_bot_with_real_trading.py"]),
]
for name, cmd in EXTS:
    if os.path.exists(cmd[-1]):
        COMMANDS.append(({"SERVICE_NAME":name}, cmd))

PROCS = []

def spawn(env_over, cmd):
    env = os.environ.copy()
    env.update(env_over)
    print(f"[launcher] start: {env.get('SERVICE_NAME','proc')} -> {' '.join(cmd)}", flush=True)
    return subprocess.Popen(cmd, env=env)

def stop_all(*_):
    print("[launcher] stopping...", flush=True)
    for p in PROCS:
        try: p.terminate()
        except: pass
    time.sleep(2)
    for p in PROCS:
        try:
            if p.poll() is None: p.kill()
        except: pass
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, stop_all)
    signal.signal(signal.SIGTERM, stop_all)

    for env_over, cmd in COMMANDS:
        PROCS.append(spawn(env_over, cmd))

    while True:
        for i, p in enumerate(list(PROCS)):
            ret = p.poll()
            if ret is not None:
                name = COMMANDS[i][0].get("SERVICE_NAME","proc")
                print(f"[launcher] {name} exited (code={ret}) → restart in 3s", flush=True)
                time.sleep(3)
                PROCS[i] = spawn(COMMANDS[i][0], COMMANDS[i][1])
        time.sleep(2)

if __name__ == "__main__":
    main()
