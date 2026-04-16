"""
SQLAlchemy async engine and session factory for test schema.
Uses SQLite in-memory for testing/demo purposes.
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class OrmBase(DeclarativeBase):
    pass


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(OrmBase.metadata.create_all)
