from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.services.base_service import BaseService
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
        self.db = BaseService()

    def handle(self):


        @self.router.message(F.content_type.in_(MEDIA_CONTENT_TYPE))
        async def any_media(message: Message):
            """При отправке медиа файла пользователю возвращается тип документа и его file_id"""

            file_id = await get_file_id_by_content_type(message)
            await message.answer(f'{message.content_type} - {file_id}')

        @self.router.message(F.text == BUTTONS['MENU'])
        async def get_menu(message: Message, state: FSMContext):
            """Отлов кнопки 'Меню' """

            data = await state.get_data()
            user = await self.db.get_user_by_tg_id(message.from_user.id)

            promocode = await self.db.get_promocode(user.promocode_id)

            chat_id = data.get('chat_id')
            delete_message_id = data.get('delete_message_id')
            delete_test_message = data.get('delete_test_message')
            video_msg = data.get('video_msg')
            video_description_msg = data.get('video_description_msg')
            msg1 = data.get('msg1')
            msg2 = data.get('msg2')
            print(f'video msg {video_msg}')

            if delete_message_id and chat_id:
                # удаляем сообщение с кнопками после нажатия на меню
                await message.bot.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('delete_message_id')
                )
                # обнуляем состояния для удаления сообщений
                await state.update_data(delete_message_id=None)

            if delete_test_message:
                await message.bot.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('delete_test_message')
                )
                await state.update_data(delete_test_message=None)

            if video_msg:
                await message.bot.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('video_msg')
                )
                await state.update_data(video_msg=None)

            if video_description_msg:
                await message.bot.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('video_description_msg')
                )
                await state.update_data(video_description_msg=None)

            if msg1:
                await message.bot.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('msg1')
                )
                await state.update_data(msg1=None)

            if msg2:
                await message.bot.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('msg2')
                )
                await state.update_data(msg2=None)

            await message.delete()
            await message.answer(
                MESSAGES['MENU'],
                reply_markup=await self.kb.start_btn(promocode)
            )

        @self.router.message(F.text)
        async def any_text(message: Message, state: FSMContext):
            """Отлавливаем любые текстовые сообщения"""

            data = await state.get_data()
            await message.answer(
                MESSAGES['ANY_TEXT'],
                reply_markup=await self.kb.start_btn(data['promocode'])
            )

