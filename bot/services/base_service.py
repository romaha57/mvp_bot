from typing import Union

from sqlalchemy import select, insert, delete, Row
from sqlalchemy.ext.asyncio import AsyncMappingResult

from bot.db_connect import async_session


class BaseService:
    """Базовый класс для общих методов работы с БД"""

    model = None

    @classmethod
    async def get_by_id(cls, id: int) -> Union[Row, None]:
        """Возвращает 1 объект по его id или None"""

        async with async_session() as session:
            query = select(cls.model.__table__.columns).filter_by(id=id)
            result = await session.execute(query)

            return result.mappings().one_or_none()

    @classmethod
    async def get_all(cls, **filters) -> AsyncMappingResult:
        """Получение всех данных из cls.model"""

        async with async_session() as session:
            query = select(cls.model.__table__.columns).filter_by(**filters)
            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def get_object_or_none(cls, **filters) -> Union[Row, None]:
        """Находит объект по фильтру или возвращает None"""

        async with async_session() as session:
            query = select(cls.model.__table__.columns).filter_by(**filters)
            result = await session.execute(query)

            return result.mappings().one_or_none()

    @classmethod
    async def create_object(cls, **data):
        """Создание объекта в БД"""

        async with async_session() as session:
            query = insert(cls.model).values(**data)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def delete(cls, id: int):
        """Удаление объекта по его id"""

        async with async_session() as session:
            query = delete(cls.model).filter_by(id=id)
            await session.execute(query)
            await session.commit()
