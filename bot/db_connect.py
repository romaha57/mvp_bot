from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from bot.settings_bot import settings


if bool(int(settings.debug)):
    db_url = settings.database_url_local
else:
    db_url = settings.database_url

engine = create_async_engine(db_url, pool_recycle=100, max_overflow=30, pool_size=10, pool_timeout=1000)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Базовый класс для создания моделей и миграций"""
    pass
