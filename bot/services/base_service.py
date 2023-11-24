from asyncio import IncompleteReadError

from sqlalchemy import select, text

from bot.db_connect import async_session
from bot.settings.model import Settings
from bot.users.models import Promocodes, Users, UserAccount


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
        """Получаем пользователя по его id"""

        async with async_session() as session:
            try:
                query = select(Users).filter_by(external_id=tg_id)
                user = await session.execute(query)

                return user.scalars().first()
            except IncompleteReadError:
                pass

    @classmethod
    async def get_account_by_tg_id(cls, tg_id: int) -> UserAccount:
        """Получаем аккаунт пользователя по его id"""

        async with async_session() as session:
            query = select(UserAccount).\
                join(Users, Users.account_id == UserAccount.id).\
                where(Users.external_id == tg_id)

            account = await session.execute(query)

            return account.scalars().first()

    @classmethod
    async def get_promocode(cls, promocode_id: int) -> Promocodes:
        """Получение промокода по его id"""

        async with async_session() as session:
            query = select(Promocodes).filter_by(id=promocode_id)
            result = await session.execute(query)

            return result.scalars().first()

