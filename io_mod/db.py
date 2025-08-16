from __future__ import annotations
import os, sqlite3, datetime as dt
from sqlalchemy import create_engine, String, Integer, Float, DateTime, JSON, Boolean
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy.pool import NullPool
from config.settings import SETTINGS

Base = declarative_base()
SessionLocal: sessionmaker[Session]

def _resolve_db_url() -> str:
    url = SETTINGS.db_url
    if url:
        return url
    pg_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if pg_url:
        return pg_url
    os.makedirs("data", exist_ok=True)
    path = "data/runtime.db"
    if not os.path.exists(path):
        con = sqlite3.connect(path); con.execute("PRAGMA journal_mode=WAL;"); con.close()
    return f"sqlite+pysqlite:///{path}"

DB_URL = _resolve_db_url()
ENGINE = create_engine(
    DB_URL, echo=False, future=True, pool_pre_ping=True,
    poolclass=NullPool if DB_URL.startswith("sqlite") else None,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, expire_on_commit=False, future=True)

class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.utcnow())
    kind: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    ts: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.utcnow())
    symbol: Mapped[str] = mapped_column(String(20))
    side: Mapped[str] = mapped_column(String(4))  # buy/sell
    qty: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16))
    paper: Mapped[bool] = mapped_column(Boolean, default=True)

class Fill(Base):
    __tablename__ = "fills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_client_id: Mapped[str] = mapped_column(String(64), index=True)
    ts: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.utcnow())
    symbol: Mapped[str] = mapped_column(String(20))
    side: Mapped[str] = mapped_column(String(4))
    qty: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)

class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True)
    qty: Mapped[float] = mapped_column(Float, default=0.0)
    avg_price: Mapped[float] = mapped_column(Float, default=0.0)

class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.utcnow())
    equity: Mapped[float] = mapped_column(Float)
    drawdown: Mapped[float] = mapped_column(Float)
    turnover: Mapped[float] = mapped_column(Float)

class Heartbeat(Base):
    __tablename__ = "heartbeats"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    component: Mapped[str] = mapped_column(String(32))
    ts: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.utcnow(), index=True)

class ErrorLog(Base):
    __tablename__ = "errors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.utcnow())
    where: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(String(400))

def init_db() -> None:
    Base.metadata.create_all(ENGINE)

def get_session() -> Session:
    return SessionLocal()

def record_heartbeat(s: Session, component: str) -> None:
    s.add(Heartbeat(component=component)); s.commit()

def record_error(s: Session, where: str, message: str) -> None:
    s.add(ErrorLog(where=where, message=message)); s.commit()

