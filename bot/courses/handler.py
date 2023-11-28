from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.courses.keyboards import CourseKeyboard
from bot.courses.service import CourseService
from bot.courses.states import CourseChooseState
from bot.handlers.base_handler import Handler
from bot.lessons.keyboards import LessonKeyboard
from bot.lessons.states import LessonChooseState
from bot.middleware import CheckPromocodeMiddleware
from bot.services.base_service import BaseService
from bot.settings.keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class CourseHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = CourseService()
        self.kb = CourseKeyboard()
        self.base_kb = BaseKeyboard()
        self.lesson_kb = LessonKeyboard()

    def handle(self):

        @self.router.message(F.text == BUTTONS['EDUCATION'])
        async def get_course(message: Message, state: FSMContext):
            """Отлов кнопки 'Обучение' и вывод списка доступынх курсов"""

            # получаем id бота текущего юзера и id курса для текущего пользователя и его промокода
            user_data = await self.db.get_bot_id_and_promocode_course_id_by_user(
                tg_id=message.from_user.id
            )

            all_courses = await self.db.get_course_by_promo_and_bot(
                bot_id=user_data['bot_id'],
                promocode_course_id=user_data['course_id']
            )

            msg1 = await message.answer(
                MESSAGES['CHOOSE_COURSE'],
                reply_markup=await self.kb.courses_btn(all_courses)
            )

            await state.update_data(msg1=msg1.message_id)
            # устанавливаем отлов состояния на название курса
            await state.set_state(CourseChooseState.course)

            menu_msg = await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=await self.base_kb.menu_btn()
            )

            await state.update_data(menu_msg=menu_msg.message_id)

        @self.router.callback_query(CourseChooseState.course, F.data)
        async def get_lesson(callback: CallbackQuery, state: FSMContext):
            """Отлавливаем выбранный пользователем курс"""

            data = await state.get_data()

            user = await self.db.get_user_by_tg_id(callback.message.chat.id)
            course = await self.db.get_course_by_name(callback.data)

            await delete_messages(
                src=callback,
                data=data,
                state=state
            )

            if course:
                # await state.clear()

                # создаем запись в истории прохождения курса со статусом 'Открыт'
                await self.db.create_history(
                    course_id=course.id,
                    tg_id=callback.message.chat.id
                )
                await callback.message.answer(course.title)
                msg = await callback.message.answer(
                    course.intro,
                    reply_markup=await self.lesson_kb.lessons_btn(course.id, user.id)
                )
                await state.update_data(chat_id=callback.message.chat.id)
                await state.update_data(delete_message_id=msg.message_id)

                menu_msg = await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )

                await state.update_data(menu_msg=menu_msg.message_id)

                # устанавливаем отлов состояния на название урока
                await state.set_state(LessonChooseState.lesson)

            else:
                await callback.message.answer(
                    MESSAGES['MENU'],
                    reply_markup=await self.base_kb.start_btn(promocode=data['promocode'])
                )
