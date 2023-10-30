from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.settings.keyboards import BaseKeyboard
from bot.utils.answers import get_file_id_by_content_type
from bot.utils.buttons import BUTTONS
from bot.utils.constants import MEDIA_CONTENT_TYPE
from bot.utils.messages import MESSAGES


class TextHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()

    def handle(self):
        @self.router.message(F.content_type.in_(MEDIA_CONTENT_TYPE))
        async def any_media(message: Message):
            """При отправке медиа файла пользователю возвращается тип документа и его file_id"""

            file_id = await get_file_id_by_content_type(message)
            await message.answer(f'{message.content_type} - {file_id}')

        @self.router.message(F.text == BUTTONS['MENU'])
        async def get_menu(message: Message, state: FSMContext):
            data = await state.get_data()
            await message.answer(
                MESSAGES['MENU'],
                reply_markup=await self.kb.start_btn(data['promocode'])
            )
