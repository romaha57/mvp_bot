from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.courses.keyboards import CourseKeyboard
from bot.courses.service import CourseService
from bot.courses.states import CourseChooseState
from bot.handlers.base_handler import Handler
from bot.utils.buttons import BUTTONS
from bot.services.base_service import BaseService
from bot.utils.messages import MESSAGES


class CourseHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = CourseService()
        self.base_db = BaseService()
        self.kb = CourseKeyboard()

    def handle(self):

        @self.router.message(F.text == BUTTONS['EDUCATION'])
        async def get_course(message: Message, state: FSMContext):
            user = await self.db.get_user_by_tg_id(message.from_user.id)
            promocode = await self.db.get_promocode(user.promocode_id)

            # получаем доступные курсы самого бота и те, которые доступны по промокоду
            courses_1 = await self.db.get_courses_ids_by_bot(user.bot_id)
            courses_2 = await self.db.get_courses_ids_by_promo(promocode.course_id)
            all_courses_ids = set(courses_1 + courses_2)
            all_courses = await self.db.get_courses(all_courses_ids)

            await message.answer(
                MESSAGES['CHOOSE_COURSE'],
                reply_markup=await self.kb.courses_btn(all_courses)
            )
            # устанавливаем отлов состояния на название курса
            await state.set_state(CourseChooseState.course)

        @self.router.message(CourseChooseState.course, F.text)
        async def get_lesson(message: Message, state: FSMContext):
            await state.clear()

            course = await self.db.get_course_by_name(message.text)

            # создаем запись в истории прохождения курса со статусом 'Открыт'
            await self.db.create_history(
                course_id=course.id,
                tg_id=message.from_user.id
            )
            await message.answer(course.title)
            await message.answer(
                course.intro,
                reply_markup=await self.kb.lessons_btn(course.id)
            )