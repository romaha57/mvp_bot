from sqlalchemy import insert, select

from bot.db_connect import async_session
from bot.services.base_service import BaseService
from bot.users.models import UserAccount, Users


class UserService(BaseService):

    @classmethod
    async def get_users_by_tg_id(cls, tg_id: int):
        """Получаем всех пользователей из таблицы $_users по их telegram_id"""

        async with async_session() as session:
            query = select(Users).filter_by(external_id=tg_id)
            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def get_or_create_account(cls, first_name: str, last_name: str):
        """Создание или получение аккаунта пользователя(аккаунт=человек)"""

        async with async_session() as session:

            query = select(UserAccount).filter_by(first_name=first_name, last_name=last_name)
            result = await session.execute(query)
            await session.commit()

            account = result.scalars().all()

            if not account:
                query = insert(UserAccount).values(
                    first_name=first_name,
                    last_name=last_name
                )
                await session.execute(query)
                await session.commit()

    @classmethod
    async def get_or_create_user(cls, username: str, tg_id: int, bot_id: int = None,
                                 promocode_id: int = None, first_name: str = None, last_name: str = None):
        """Создание или получение пользователя из БД"""

        user = await cls.get_users_by_tg_id(
            tg_id=tg_id
        )
        if not user:
            await cls.get_or_create_account(
                first_name=first_name,
                last_name=last_name
            )

            async with async_session() as session:
                query = insert(Users).values(
                    username=username,
                    bot_id=bot_id,
                    external_id=tg_id,
                    promocode_id=promocode_id
                )
                await session.execute(query)
                await session.commit()
