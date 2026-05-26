from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_timeout=5,
    pool_size = 20,
    max_overflow=10,
    pool_recycle=1800,
    connect_args={
        "timeout": 5,
        "statement_cache_size": 0,
        "server_settings": {
            "statement_timeout": "3000",  # 3초 이상 걸리는 쿼리는 강제 종료
            "idle_in_transaction_session_timeout": "7000" # 트랜잭션 열고 7초간 대기 시 종료
        }
    },
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise