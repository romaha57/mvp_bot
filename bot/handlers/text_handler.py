import traceback

from aiogram import Bot, F, Router
from aiogram.filters import and_f, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.handlers.base_handler import Handler
from bot.lessons.states import LessonChooseState
from bot.services.base_service import BaseService
from bot.settings.keyboards import BaseKeyboard
from bot.utils.answers import get_file_id_by_content_type
from bot.utils.buttons import BUTTONS
from bot.utils.constants import MEDIA_CONTENT_TYPE
from bot.utils.delete_messages import delete_messages
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

            try:

                file_id = await get_file_id_by_content_type(message)
                await message.answer(f'{message.content_type} - <b>{file_id}</b>')

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.message(or_f(F.text.startswith(BUTTONS['MENU']),
                                  and_f(F.text.startswith(BUTTONS['MENU']), LessonChooseState.lesson)))
        async def get_menu(message: Message, state: FSMContext):
            """Отлов кнопки 'Меню' """

            try:

                # обнуляем отлов состояний
                await state.set_state(state=None)

                data = await state.get_data()
                logger.debug(f"Пользователь {message.from_user.id}, состояние: {data}, отлов: {await state.get_state()}")
                promocode = await self.db.get_promocode_by_tg_id(message.from_user.id)
                if promocode:

                    await delete_messages(
                        src=message,
                        data=data,
                        state=state
                    )

                    await message.delete()
                    menu_msg = await message.answer(
                        MESSAGES['MENU'],
                        reply_markup=await self.kb.start_btn(promocode)
                    )
                    await state.update_data(menu_msg=menu_msg.message_id)
                else:
                    await message.answer(
                        MESSAGES['ERROR_PROMOCODE'],
                        reply_markup=await self.kb.menu_btn()
                    )

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.message(F.text)
        async def any_text(message: Message, state: FSMContext):
            """Отлавливаем любые текстовые сообщения"""

            try:
                data = await state.get_data()

                logger.debug(f"Пользователь {message.from_user.id}, состояние: {data}, отлов: {await state.get_state()}")

                promocode = await self.db.get_promocode_by_tg_id(message.from_user.id)
                await message.answer(
                    MESSAGES['ANY_TEXT'],
                    reply_markup=await self.kb.start_btn(promocode)
                )

            except Exception:
                logger.warning(traceback.format_exc())
