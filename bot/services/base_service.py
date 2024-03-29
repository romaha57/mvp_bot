from asyncio import IncompleteReadError

from sqlalchemy import select, update, text, insert

from bot.db_connect import async_session
from bot.settings.model import Settings
from bot.users.models import Promocodes, UserAccount, Users, AnketaAnswers


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
        """Получение id бота для дальнейнего получения всех курсов"""

        async with async_session() as session:
            query = select(Users.bot_id).where(Users.external_id == tg_id)
            result = await session.execute(query)

            return result.mappings().first()

    @classmethod
    async def get_promocode_by_tg_id(cls, tg_id: int) -> Promocodes:
        """Получаем промокод по telegram_id"""

        async with async_session() as session:
            query = select(Promocodes).\
                join(Users, Users.promocode_id == Promocodes.id).\
                where(Users.external_id == tg_id)

            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def add_promocode_to_user(cls, tg_id: int, promocode_id: int):
        """Добавляем пользователю промокод"""

        async with async_session() as session:
            query = update(Users).where(Users.external_id == tg_id).values(promocode_id=promocode_id)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_promocode_courses_and_quizes(cls, promocode_id: int) -> dict:
        """Получаем все доступные курсы и квизы для промокода"""

        async with async_session() as session:
            query = text(f"""
                  SELECT $_promocodes.type_id promocode_type, group_concat(DISTINCT $_promocodes_courses.course_id) courses, group_concat(DISTINCT $_promocodes_quizes.quiz_id) quizes
                  FROM $_promocodes
                  LEFT JOIN $_promocodes_courses ON $_promocodes_courses.promocode_id = $_promocodes.id
                  LEFT JOIN $_promocodes_quizes ON $_promocodes_quizes.promocode_id = $_promocodes.id
                  WHERE $_promocodes.id = {promocode_id}
              """)

            res = await session.execute(query)
            return res.mappings().first()

    @classmethod
    async def save_user_anketa_answer(cls, question_id: int, answer: str, account_id: int):

        async with async_session() as session:
            query = insert(AnketaAnswers).values(
                question_id=question_id,
                account_id=account_id,
                answer=answer
            )
            await session.execute(query)
            await session.commit()
