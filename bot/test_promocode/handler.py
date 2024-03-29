from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.courses.keyboards import CourseKeyboard
from bot.courses.service import CourseService
from bot.courses.states import CourseChooseState
from bot.handlers.base_handler import Handler
from bot.quiz.keyboads import QuizKeyboard
from bot.quiz.service import QuizService
from bot.quiz.states import QuizState
from bot.services.base_service import BaseService
from bot.settings.keyboards import BaseKeyboard
from bot.test_promocode.keyboards import TestPromoKeyboard
from bot.test_promocode.utils import is_valid_test_promo
from bot.utils.buttons import BUTTONS
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class TestPromoHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = BaseService()
        self.quiz_db = QuizService()
        self.course_db = CourseService()
        self.kb = TestPromoKeyboard()
        self.base_kb = BaseKeyboard()
        self.quiz_kb = QuizKeyboard()
        self.course_kb = CourseKeyboard()

    def handle(self):

        @self.router.message(F.text == BUTTONS['TEST_QUIZ'])
        async def start_test_quiz(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            await delete_messages(
                src=message,
                data=data,
                state=state
            )
            user = await self.db.get_user_by_tg_id(message.chat.id)
            if is_valid_test_promo(user):

                quizes_by_bot = await self.quiz_db.get_quizes_by_bot(message.chat.id)
                quizes_by_db = await self.quiz_db.get_all_quizes()
                all_quizes = list(set(quizes_by_bot + quizes_by_db))
                all_quizes.sort(key=lambda elem: elem.get('id'))

                await message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )

                msg = await message.answer(
                    MESSAGES['CHOOSE_QUIZ'],
                    reply_markup=await self.quiz_kb.quizes_list_btn(all_quizes)
                )
                await state.set_state(QuizState.quiz)
                await state.update_data(msg=msg.message_id)

            else:
                await message.answer(
                    MESSAGES['END_TEST_PERIOD'],
                    reply_markup=await self.kb.test_promo_menu()
                )

        @self.router.message(F.text == BUTTONS['TEST_EDUCATION'])
        async def start_test_education(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages(
                src=message,
                data=data,
                state=state
            )
            user = await self.db.get_user_by_tg_id(message.chat.id)
            if is_valid_test_promo(user):
                courses_by_bot = await self.course_db.get_courses_by_bot(message.chat.id)
                courses_by_db = await self.course_db.get_all_courses()
                all_courses = list(set(courses_by_bot + courses_by_db))
                all_courses.sort(key=lambda elem: elem.get('id'))

                msg = await message.answer(
                    MESSAGES['CHOOSE_COURSE'],
                    reply_markup=await self.course_kb.courses_btn(all_courses)
                )

                await state.update_data(msg=msg.message_id)
                await state.set_state(CourseChooseState.course)

            else:
                await message.answer(
                    MESSAGES['END_TEST_PERIOD'],
                    reply_markup=await self.kb.test_promo_menu()
                )