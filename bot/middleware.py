from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.users.service import UserService
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class CheckPromocodeMiddleware(BaseMiddleware):
    """Мидлварь для проверку на активность промокода
    Если прмокод не активен, то выводим сообщение об ошибке
    """

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:

        tg_id = data['event_from_user'].id
        # получаем промокод текущего пользователя
        # и если он активен, то идем дальше в хендлер
        # если нет, то выводим сообщение(сообщения срабатывают на все, кроме inline взаимодействия)
        promocode = await UserService.get_promocode_by_tg_id(tg_id)
        if promocode.actual:
            result = await handler(event, data)
            return result

        else:
            state_data = await data['state'].get_data()

            # удаление оставшихся сообщений с кнопками
            await delete_messages(
                data=state_data,
                state=data['state'],
                src=data['bot']
            )
            await event.answer(
                MESSAGES['WRONG_PROMOCODE'],
                show_alert=True
            )
