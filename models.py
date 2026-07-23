"""Асинхронный слой хранения данных на SQLAlchemy (async).

Заменяет синхронный словарь на полноценное асинхронное хранилище.
По умолчанию используется SQLite через aiosqlite (удобно для локального запуска),
а в Docker через переменную окружения DB_DSN подключается PostgreSQL (asyncpg).
"""
import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# DSN можно переопределить через переменную окружения (в docker-compose это PostgreSQL).
DB_DSN = os.getenv("DB_DSN", "sqlite+aiosqlite:///./app.db")

engine = create_async_engine(DB_DSN, echo=False)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    advertisements: Mapped[list["Advertisement"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Advertisement(Base):
    __tablename__ = "advertisements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=func.now()
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="advertisements")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "owner": self.owner_id,
        }


async def init_db() -> None:
    """Создать таблицы (вызывается при старте приложения)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Закрыть пул соединений (вызывается при остановке приложения)."""
    await engine.dispose()
