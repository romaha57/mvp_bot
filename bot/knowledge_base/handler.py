import traceback
import datetime

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from loguru import logger

from bot.handlers.base_handler import Handler
from bot.knowledge_base.keyboards import KnowledgeKeyboard
from bot.knowledge_base.service import KnowledgeService
from bot.settings.keyboards import BaseKeyboard
from bot.test_promocode.keyboards import TestPromoKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class KnowledgeHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = KnowledgeService()
        self.kb = KnowledgeKeyboard()
        self.promo_kb = TestPromoKeyboard()
        self.base_kb = BaseKeyboard()

    def handle(self):

        @self.router.message(F.text.startswith(BUTTONS['KNOWLEDGE_BASE']))
        async def knowledge_base_menu(message: Message, state: FSMContext):
            """Стартовое меню базы знаний"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)

            if promocode.is_test:
                msg_text = await self.db.get_msg_by_key('KNOWLEDGE_BASE_CLOSED')
                await message.answer(
                    msg_text,
                    reply_markup=await self.promo_kb.test_promo_menu()
                )
            else:

                if promocode.end_at <= datetime.datetime.now():
                    courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                    msg_text = await self.db.get_msg_by_key('YOUR_PROMOCODE_IS_EXPIRED')
                    await message.answer(
                        msg_text,
                        reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                    )
                else:

                    await delete_messages(
                        src=message,
                        data=data,
                        state=state
                    )

                    root_divides = await self.db.get_root_divides()

                    msg_text = await self.db.get_msg_by_key('KNOWLEDGE_MENU')
                    msg = await message.answer(
                        msg_text,
                        reply_markup=self.kb.divides_menu(root_divides)
                    )
                    await state.update_data(base_msg=msg.message_id)
                    await state.update_data(chat_id=message.chat.id)

        @self.router.callback_query(F.data.startswith('divide'))
        async def get_nested_divide(callback: CallbackQuery, state: FSMContext):
            """Получение вложенной папки"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                msg_text = await self.db.get_msg_by_key('YOUR_PROMOCODE_IS_EXPIRED')
                await callback.message.answer(
                    msg_text,
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

                root_divide_id = callback.data.split('_')[-1]

                divides = await self.db.get_divides_by_root(root_divide_id)
                files = await self.db.get_files_by_divide(root_divide_id)

                if data.get('base_msg'):
                    await callback.bot.edit_message_reply_markup(
                        chat_id=data.get('chat_id'),
                        message_id=data.get('base_msg'),
                        reply_markup=self.kb.divides_menu(divides, files)
                    )

        @self.router.callback_query(F.data.startswith('file'))
        async def get_knowledge_base_file(callback: CallbackQuery, state: FSMContext):
            """Получение файла базы знаний"""

            await state.update_data(chat_id=callback.message.chat.id)

            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                msg_text = await self.db.get_msg_by_key('YOUR_PROMOCODE_IS_EXPIRED')
                await callback.message.answer(
                    msg_text,
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

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

        @self.router.callback_query(F.data.startswith('baseback'))
        async def back_button(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки нахад в меню базы знаний"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                msg_text = await self.db.get_msg_by_key('YOUR_PROMOCODE_IS_EXPIRED')
                await callback.message.answer(
                    msg_text,
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

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
