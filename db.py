import json
import os
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String, Column, DateTime, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from utils import _IS_LOCAL, formater_date_iso
from logging import getLogger
logger = getLogger(__name__)

class Base(DeclarativeBase):
    pass


class TodoORM(Base):
    __tablename__ = "todos"

    id = Column(String(32), primary_key=True, index=True)
    title = Column(String(120), nullable=False)
    description = Column(String(250), default="", nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def _read_postgres_uri() -> str | None:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    raw_vcap = os.getenv("VCAP_SERVICES")
    if not raw_vcap:
        return None

    try:
        services = json.loads(raw_vcap)
    except json.JSONDecodeError:
        return None

    for service_name in ("postgresql-db", "postgres", "postgresql"):
        candidates = services.get(service_name, [])
        for candidate in candidates:
            credentials = candidate.get("credentials") or {}
            uri = credentials.get("uri")
            if uri:
                return uri

    return None


class BDWrapper:
    def __init__(self) -> None:
        self.mode = "sqlite"
        self.fallback_reason = None
        self.engine = self._build_engine()
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        Base.metadata.create_all(bind=self.engine)

    def _build_engine(self):
        postgres_uri = _read_postgres_uri()

        if not _IS_LOCAL and postgres_uri:
            try:
                engine = create_engine(postgres_uri, pool_pre_ping=True, future=True)
                with engine.connect() as connection:
                    connection.execute("SELECT 1")
                self.mode = "postgres"
                return engine
            except SQLAlchemyError as exc:
                logger.error(f"Postgres indisponible: {exc}")
                self.fallback_reason = f"Postgres indisponible: {exc}"

        sqlite_uri = "sqlite:///./todos.db"
        self.mode = "sqlite"
        return create_engine(sqlite_uri, connect_args={"check_same_thread": False}, future=True)

    def list_todos(self) -> list[dict[str, Any]]:
        try:
            with self.SessionLocal() as session:
                rows = session.query(TodoORM).order_by(TodoORM.created_at.desc()).all()
                return [
                    {
                        "id": row.id,
                        "title": row.title,
                        "description": row.description,
                        "created_at": formater_date_iso(row.created_at.isoformat(timespec="seconds")),
                    }
                    for row in rows
                ]
        except SQLAlchemyError:
            return []

    def create_todo(self, title: str, description: str) -> dict[str, Any]:
        record = TodoORM(
            id=str(uuid.uuid4())[:8],
            title=title.strip(),
            description=description.strip(),
            created_at=datetime.now().replace(microsecond=0),
        )

        try:
            with self.SessionLocal() as session:
                session.add(record)
                session.commit()
                session.refresh(record)
        except SQLAlchemyError:
            return {
                "id": record.id,
                "title": record.title,
                "description": record.description,
                "created_at": record.created_at.isoformat(timespec="seconds"),
            }

        return {
            "id": record.id,
            "title": record.title,
            "description": record.description,
            "created_at": record.created_at.isoformat(timespec="seconds"),
        }

    def delete_todo(self, todo_id: str) -> bool:
        try:
            with self.SessionLocal() as session:
                row = session.get(TodoORM, todo_id)
                if row is None:
                    return False
                session.delete(row)
                session.commit()
                return True
        except SQLAlchemyError:
            return False


_todo_db = BDWrapper()


def get_todo_db() -> BDWrapper:
    return _todo_db
