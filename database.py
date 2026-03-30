import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Коли запускаємо локально (не в докері), щоб не падав додаток, робимо fallback на SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./library.db")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
