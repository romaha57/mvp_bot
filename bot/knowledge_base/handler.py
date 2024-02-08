import traceback

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.handlers.base_handler import Handler
from bot.knowledge_base.keyboards import KnowledgeKeyboard
from bot.knowledge_base.service import KnowledgeService
from bot.settings.keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class KnowledgeHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = KnowledgeService()
        self.kb = KnowledgeKeyboard()
        self.base_kb = BaseKeyboard()

    def handle(self):

        @self.router.message(F.text.startswith(BUTTONS['KNOWLEDGE_BASE']))
        async def knowledge_base_menu(message: Message, state: FSMContext):
            """Стартовое меню базы знаний"""

            try:

                root_divides = await self.db.get_root_divides()

                msg = await message.answer(
                    MESSAGES['KNOWLEDGE_MENU'],
                    reply_markup=self.kb.divides_menu(root_divides)
                )
                await state.update_data(base_msg=msg.message_id)
                await state.update_data(chat_id=message.chat.id)

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.callback_query(F.data.startswith('divide'))
        async def get_nested_divide(callback: CallbackQuery, state: FSMContext):
            """Получение вложенной папки"""

            try:

                data = await state.get_data()

                root_divide_id = callback.data.split('_')[-1]

                divides = await self.db.get_divides_by_root(root_divide_id)
                files = await self.db.get_files_by_divide(root_divide_id)

                if data.get('base_msg'):
                    await callback.bot.edit_message_reply_markup(
                        chat_id=data.get('chat_id'),
                        message_id=data.get('base_msg'),
                        reply_markup=self.kb.divides_menu(divides, files)
                    )

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.callback_query(F.data.startswith('file'))
        async def get_knowledge_base_file(callback: CallbackQuery, state: FSMContext):
            """Получение файла базы знаний"""

            try:

                file_id = callback.data.split('_')[-1]

                file = await self.db.get_file_by_id(file_id)
                file_text = file.title
                if file.description:
                    file_text += f'\n{file.description}'

                if file.type_id == 1:
                    await callback.message.answer_document(
                        document=file.document,
                        caption=file_text
                    )

                elif file.type_id == 2:
                    await callback.message.answer_video(
                        video=file.document,
                        caption=file_text
                    )

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.callback_query(F.data.startswith('baseback'))
        async def back_button(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки нахад в меню базы знаний"""
            try:

                data = await state.get_data()
                parent_id = callback.data.split('_')[-1]
                parent_id = int(parent_id) - 1

                divides = await self.db.get_divides_by_root(parent_id)
                files = await self.db.get_files_by_divide(parent_id)

                if data.get('base_msg'):
                    await callback.bot.edit_message_reply_markup(
                        chat_id=data.get('chat_id'),
                        message_id=data.get('base_msg'),
                        reply_markup=self.kb.divides_menu(divides, files)
                    )

            except Exception:
                logger.warning(traceback.format_exc())
