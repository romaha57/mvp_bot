from sqlalchemy import select

from bot.db_connect import async_session
from bot.services.base_service import BaseService
from bot.settings.model import Settings
from bot.users.models import Promocodes


class SettingsService(BaseService):
    model = Settings

    @classmethod
    async def check_promocode(cls, promocode: str):
        """Проверяем сущестует ли промокод в БД"""

        async with async_session() as session:
            query = select(Promocodes).filter_by(code=promocode)
            result = await session.execute(query)

            return result.scalars().one_or_none()
