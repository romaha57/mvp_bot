from typing import Union

from sqlalchemy import Row, select

from bot.db_connect import async_session
from bot.settings.model import Settings
from bot.users.models import Promocodes, Users


class BaseService:
    """Базовый класс для общих методов работы с БД"""

    @classmethod
    async def get_msg_by_key(cls, key: str) -> str:
        """Получение сообщение бота по его ключу"""

        async with async_session() as session:
            query = select(Settings.value).filter_by(key=key)
            result = await session.execute(query)

            return str(result.scalar())

    @classmethod
    async def get_user_by_tg_id(cls, tg_id: int) -> Users:
        async with async_session() as session:
            query = select(Users).filter_by(external_id=tg_id)
            user = await session.execute(query)

            return user.scalars().one()

    @classmethod
    async def get_promocode(cls, promocode_id: int) -> Promocodes:
        """Получение промокода по его id"""

        async with async_session() as session:
            query = select(Promocodes).filter_by(id=promocode_id)
            result = await session.execute(query)

            return result.scalars().one()
