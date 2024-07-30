from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from loguru import logger

from bot.services.base_service import BaseService
from bot.users.service import UserService
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class MarkUserLastActionMiddleware(BaseMiddleware):
    """
    Отмечаем каждое действие пользотваеля

    """

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:

        try:
            tg_id = data['event_from_user'].id
            await UserService.mark_last_action(tg_id)
        except Exception as e:
            logger.warning(f'При last_action ошибка: {e}')
        finally:
            result = await handler(event, data)
            return result
