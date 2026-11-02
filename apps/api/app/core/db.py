import os
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, url: str):
        self.url = url
        kwargs = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            if url == "sqlite://":
                kwargs["poolclass"] = StaticPool
        self.engine = create_engine(url, **kwargs)
        if url.startswith("sqlite"):

            @event.listens_for(self.engine, "connect")
            def _fk_on(dbapi_conn, _):
                dbapi_conn.execute("PRAGMA foreign_keys=ON")

        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    def session(self) -> Session:
        return self.SessionLocal()

    def create_all(self) -> None:
        if self.url.startswith("sqlite:///"):
            raw = self.url.split("sqlite:///", 1)[1]
            if raw and raw != ":memory:":
                os.makedirs(os.path.dirname(raw) or ".", exist_ok=True)
        Base.metadata.create_all(self.engine)

    def reset(self) -> None:
        """Drop and recreate all tables (demo reset only)."""
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)


def get_db(request: Request):
    db: Session = request.app.state.db.SessionLocal()
    try:
        yield db
    finally:
        db.close()
