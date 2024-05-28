import datetime
import pprint
import traceback

from aiogram import Bot, F, Router
from aiogram.filters import and_f, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.handlers.base_handler import Handler
from bot.lessons.states import LessonChooseState
from bot.services.base_service import BaseService
from bot.settings.keyboards import BaseKeyboard
from bot.test_promocode.keyboards import TestPromoKeyboard
from bot.test_promocode.utils import is_valid_test_promo
from bot.users.states import Anketa
from bot.utils.answers import get_file_id_by_content_type, check_user_anket, show_main_menu
from bot.utils.buttons import BUTTONS
from bot.utils.constants import MEDIA_CONTENT_TYPE
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class TextHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()
        self.test_promo_kb = TestPromoKeyboard()
        self.db = BaseService()
        self.anketa_questions = None

    def handle(self):

        @self.router.message(F.content_type.in_(MEDIA_CONTENT_TYPE))
        async def any_media(message: Message):
            """При отправке медиа файла пользователю возвращается тип документа и его file_id"""

            pprint.pprint(message)
            file_id, file_type_id, label = await get_file_id_by_content_type(message)
            await self.db.save_file_id(
                label=label,
                file_id=file_id,
                attachment_type=file_type_id

            )
            await message.answer(
                f'{message.content_type} - <b>{file_id}</b>'
            )

        @self.router.message(or_f(F.text.startswith(BUTTONS['MENU']),
                                  and_f(F.text.startswith(BUTTONS['MENU']), LessonChooseState.lesson)))
        async def get_menu(message: Message, state: FSMContext):
            """Отлов кнопки 'Меню' """

            await state.set_state(state=None)
            await state.update_data(chat_id=message.chat.id)

            data = await state.get_data()

            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            user = await self.db.get_user_by_tg_id(message.chat.id)
            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)

            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                await message.answer(
                    MESSAGES['YOUR_PROMOCODE_IS_EXPIRED'],
                    reply_markup=await self.kb.start_btn(courses_and_quizes)
                )

            else:

                anketa_questions = await check_user_anket(
                    message=message,
                    user=user
                )
                if anketa_questions:
                    await get_user_answers_for_anketa(
                        message=message,
                        state=state,
                        questions=anketa_questions
                    )
                else:
                    if promocode:
                        await show_main_menu(
                            message=message,
                            state=state,
                            self=self,
                            promocode=promocode,
                            user=user
                        )

                    else:
                        await message.answer(
                            MESSAGES['ERROR_PROMOCODE'],
                            reply_markup=await self.kb.menu_btn()
                        )

        @self.router.callback_query(F.data.startswith('menu'))
        async def get_menus(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки 'Меню' """

            await state.set_state(state=None)
            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages(
                src=callback.message,
                data=data,
                state=state
            )

            logger.debug(
                f"Пользователь {callback.message.chat.id} перешел в меню по INLINE")
            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)

            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                await callback.message.answer(
                    MESSAGES['YOUR_PROMOCODE_IS_EXPIRED'],
                    reply_markup=await self.kb.start_btn(courses_and_quizes)
                )
            else:

                user = await self.db.get_user_by_tg_id(callback.message.chat.id)
                if promocode:
                    await show_main_menu(
                        message=callback.message,
                        state=state,
                        self=self,
                        promocode=promocode,
                        user=user
                    )

                else:
                    await callback.message.answer(
                        MESSAGES['ERROR_PROMOCODE'],
                        reply_markup=await self.kb.menu_btn()
                    )

        @self.router.message(F.text == BUTTONS['HELP'])
        async def help_user(message: Message, state: FSMContext):
            await state.update_data(chat_id=message.chat.id)

            await message.answer(
                MESSAGES['SUPPORT'],
                reply_markup=await self.kb.help_btn()
            )

        async def get_user_answers_for_anketa(message: Message, state: FSMContext, questions: list[dict]):
            await message.answer(
                MESSAGES['START_ANKETA']
            )

            self.anketa_questions = questions
            first_question = self.anketa_questions.pop()
            await message.answer(
                MESSAGES['ANKETA_QUESTION'].format(
                    first_question.get('title')
                )
            )
            await state.update_data(anketa_question_id=first_question.get('id'))
            await state.set_state(Anketa.answer)

            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=await self.kb.menu_btn()
            )

        @self.router.message(Anketa.answer)
        async def get_anketa_answer(message: Message, state: FSMContext):

            user = await self.db.get_user_by_tg_id(message.chat.id)
            data = await state.get_data()
            question_id = data.get('anketa_question_id')
            answer = message.text
            account = await self.db.get_account_by_tg_id(message.chat.id)

            await self.db.save_user_anketa_answer(
                question_id=question_id,
                answer=answer,
                account_id=account.id
            )
            self.anketa_questions = await check_user_anket(
                        message=message,
                        user=user
                    )

            await message.answer(
                MESSAGES['YOUR_ANSWER_SAVE']
            )

            try:
                anketa_question = self.anketa_questions.pop()
                await message.answer(
                    MESSAGES['ANKETA_QUESTION'].format(
                        anketa_question.get('title')
                    )
                )
                await state.update_data(anketa_question_id=anketa_question.get('id'))
                await state.set_state(Anketa.answer)

            except (IndexError, AttributeError):
                await state.set_state(state=None)
                promocode = await self.db.get_promocode_by_tg_id(message.from_user.id)
                user = await self.db.get_user_by_tg_id(message.chat.id)

                if promocode.is_test:
                    if is_valid_test_promo(user):
                        await message.answer(
                            MESSAGES['TEST_PROMO_MENU'],
                            reply_markup=await self.test_promo_kb.test_promo_menu()
                        )

                    else:
                        await message.answer(
                            MESSAGES['END_TEST_PERIOD'],
                            reply_markup=await self.test_promo_kb.test_promo_menu()
                        )
                        await state.set_state(state=None)

                else:
                    courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                    await message.answer(
                        MESSAGES['ANY_TEXT'],
                        reply_markup=await self.kb.start_btn(courses_and_quizes)
                    )

        @self.router.message(F.text)
        async def any_text(message: Message, state: FSMContext):
            """Отлавливаем любые текстовые сообщения"""

            await state.set_state(state=None)
            await state.update_data(chat_id=message.chat.id)

            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)

            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                await message.answer(
                    MESSAGES['YOUR_PROMOCODE_IS_EXPIRED'],
                    reply_markup=await self.kb.start_btn(courses_and_quizes)
                )
            else:

                user = await self.db.get_user_by_tg_id(message.chat.id)

                if promocode.is_test:
                    if is_valid_test_promo(user):
                        await message.answer(
                            MESSAGES['TEST_PROMO_MENU'],
                            reply_markup=await self.test_promo_kb.test_promo_menu()
                        )

                    else:
                        await message.answer(
                            MESSAGES['END_TEST_PERIOD'],
                            reply_markup=await self.test_promo_kb.test_promo_menu()
                        )
                        await state.set_state(state=None)

                elif promocode.type_id == 3:
                    await message.answer(
                        MESSAGES['START_PROMOCODE_OWNER'],
                        reply_markup=await self.kb.start_btn(promocode))

                else:
                    courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                    await message.answer(
                        MESSAGES['ANY_TEXT'],
                        reply_markup=await self.kb.start_btn(courses_and_quizes)
                    )
