from sqlalchemy import select

from bot.db_connect import async_session
from bot.services.base_service import BaseService
from bot.settings.model import Settings


class SettingsService(BaseService):
    model = Settings

    @classmethod
    async def get_msg_by_key(cls, key: str):
        """Получение сообщение бота по его ключу"""

        async with async_session() as session:
            query = select(cls.model.value).filter_by(key=key)
            result = await session.execute(query)

            return str(result.scalar())
