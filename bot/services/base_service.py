from asyncio import IncompleteReadError

from sqlalchemy import select

from bot.db_connect import async_session
from bot.settings.model import Settings
from bot.users.models import Promocodes, UserAccount, Users


class Singleton(type):
    """Синглтон для БД"""

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class BaseService(metaclass=Singleton):
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

    @classmethod
    async def get_bot_id_and_promocode_course_id_by_user(cls, tg_id: int):
        """Получение id бота и курс к данному промокоду для дальнейнего получения всех курсов"""

        async with async_session() as session:
            query = select(Users.bot_id, Promocodes.course_id).\
                select_from(Users).\
                join(Promocodes, Users.promocode_id == Promocodes.id). \
                where(Users.external_id == tg_id)

            result = await session.execute(query)

            return result.mappings().first()

    @classmethod
    async def get_promocode_by_tg_id(cls, tg_id: int):
        """Получаем промокод по telegram_id"""

        async with async_session() as session:
            query = select(Promocodes).\
                join(Users, Users.promocode_id == Promocodes.id).\
                where(Users.external_id == tg_id)

            result = await session.execute(query)

            return result.scalars().first()
