from typing import Union

from sqlalchemy import select, insert, delete, Row, text
from sqlalchemy.ext.asyncio import AsyncMappingResult

from bot.db_connect import async_session
from bot.settings.model import Settings
from bot.users.models import Users, Promocodes


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


    @classmethod
    async def test(cls):
        async with async_session() as session:
            query = text('SELECT 1 ')
            result = await session.execute(query)

            return str(result.scalar())
    @classmethod
    async def get_msg_by_key(cls, key: str):
        """Получение сообщение бота по его ключу"""

        async with async_session() as session:
            query = select(Settings.value).filter_by(key=key)
            result = await session.execute(query)

            return str(result.scalar())

    @classmethod
    async def get_user_by_tg_id(cls, tg_id: int):
        async with async_session() as session:
            query = select(Users).filter_by(external_id=tg_id)
            user = await session.execute(query)

            return user.scalars().one()

    @classmethod
    async def get_promocode(cls, promocode_id: int):
        """Получение промокода по его id"""

        async with async_session() as session:
            query = select(Promocodes).filter_by(id=promocode_id)
            result = await session.execute(query)

            return result.scalars().one()
