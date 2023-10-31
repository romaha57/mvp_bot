import pprint

from aiogram.types import Message
from sqlalchemy import select, insert

from bot.db_connect import async_session
from bot.services.base_service import BaseService
from bot.users.models import Users, UserAccount


class UserService(BaseService):
    model = Users

    @classmethod
    async def get_or_create_user(cls, username: str, tg_id: int, bot_id: int = None, promocode_id: int = None):
        user = await cls.get_object_or_none(
            username=username
        )
        if not user:
            async with async_session() as session:
                query = insert(Users).values(
                    username=username,
                    bot_id=bot_id,
                    external_id=tg_id,
                    promocode_id=promocode_id
                )
                await session.execute(query)
                await session.commit()

