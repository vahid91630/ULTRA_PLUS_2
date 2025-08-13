from __future__ import annotations
from pymongo import MongoClient, ASCENDING, DESCENDING
class DB:
    def __init__(self, url: str):
        self.client = MongoClient(url)
        self.db = self.client["ultra"]
        self.heartbeats = self.db["heartbeats"]
        self.ticker = self.db["ticker"]
        self.equity = self.db["equity"]
        self.signals = self.db["signals"]
        self.raw = self.db["raw_events"]
        self.scored = self.db["scored_events"]
        self.trades = self.db["trades"]
        self._ensure()
    def _ensure(self):
        self.heartbeats.create_index([("service", ASCENDING)], unique=True)
        self.heartbeats.create_index([("ts", DESCENDING)])
        self.ticker.create_index([("ts", DESCENDING)])
        self.equity.create_index([("ts", DESCENDING)])
        self.signals.create_index([("ts", DESCENDING)])
        self.trades.create_index([("ts", DESCENDING)])
