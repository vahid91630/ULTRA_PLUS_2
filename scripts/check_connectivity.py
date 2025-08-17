#!/usr/bin/env python3
"""Quick connectivity & readiness report.
Prints:
- Environment mode & symbol
- Presence of required MEXC keys
- Attempt real exchange instantiation (no trading)
- Paper broker sanity roundtrip
"""
import os, json, sys, pathlib

# Ensure project root on path when running as standalone script
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import SETTINGS
from exchange_mexc import make_exchange_if_available, make_broker

def main():
    report = {
        'mode': SETTINGS.mode,
        'symbol': SETTINGS.symbol,
        'have_api_key': bool(SETTINGS.api_key),
        'have_api_secret': bool(SETTINGS.api_secret),
        'env_api_key_set': bool(os.getenv('MEXC_API_KEY') or os.getenv('API_KEY')),
        'env_api_secret_set': bool(os.getenv('MEXC_API_SECRET') or os.getenv('MEXC_SECRET_KEY') or os.getenv('SECRET')),
        'missing': [],
    }
    if not report['have_api_key']: report['missing'].append('MEXC_API_KEY')
    if not report['have_api_secret']: report['missing'].append('MEXC_API_SECRET or MEXC_SECRET_KEY')
    ex = make_exchange_if_available()
    report['exchange_object_created'] = ex is not None

    # Paper broker test
    broker = make_broker()
    o,f = broker.create_market_order('BTC/USDT','buy',0.01,100)
    o2,f2 = broker.create_market_order('BTC/USDT','sell',0.01,100)
    report['paper_roundtrip_ok'] = (broker.pos_qty == 0)

    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
