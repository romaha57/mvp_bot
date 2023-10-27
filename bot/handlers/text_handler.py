from aiogram import Router, Bot, F
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.utils.answers import get_file_id_by_content_type
from bot.utils.constants import MEDIA_CONTENT_TYPE


class TextHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()

    def handle(self):
        @self.router.message(F.content_type.in_(MEDIA_CONTENT_TYPE))
        async def any_media(message: Message):
            """При отправке медиа файла пользователю возвращается тип документа и его file_id"""

            file_id = await get_file_id_by_content_type(message)
            await message.answer(f'{message.content_type} - {file_id}')
