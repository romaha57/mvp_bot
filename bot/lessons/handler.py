import json

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.courses.service import CourseService
from bot.handlers.base_handler import Handler
from bot.lessons.keyboards import LessonKeyboard
from bot.lessons.service import LessonService
from bot.lessons.states import LessonChooseState
from bot.settings.keyboards import BaseKeyboard
from bot.utils.messages import MESSAGES


class LessonHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = LessonService()
        self.course_db = CourseService()
        self.kb = LessonKeyboard()
        self.base_kb = BaseKeyboard()
        self.test_questions = None

    def handle(self):

        @self.router.message(LessonChooseState.lesson, F.text)
        async def choose_lesson(message: Message, state: FSMContext):
            await state.clear()
            lesson = await self.db.get_lesson_by_name(message.text)
            user = await self.db.get_user_by_tg_id(message.from_user.id)

            # получаем актуальную для текущего пользователя попытку прохождения курса
            actual_course_attempt = await self.course_db.get_actual_course_attempt(
                user_id=user.id,
                course_id=lesson.course_id
            )

            # создаем запись истории прохождения урока
            await self.db.create_history(
                lesson_id=lesson.id,
                user_id=user.id,
                course_history_id=actual_course_attempt.id
            )

            if lesson:
                if lesson.video:
                    await message.answer_video(
                        lesson.video,
                        caption=lesson.title
                    )
                    await message.answer(
                        lesson.description,
                        reply_markup=await self.kb.lesson_menu_btn(lesson.course_id)
                    )

                else:
                    await message.answer(lesson.title)
                    await message.answer(
                        lesson.description,
                        reply_markup=await self.kb.lesson_menu_btn(lesson.course_id)
                    )

            else:
                await message.answer(MESSAGES['NOT_FOUND_LESSON'])

            # состояние на прохождение теста после урока
            await state.set_state(LessonChooseState.start_test)
            await state.update_data(lesson=lesson)

        @self.router.callback_query(F.data.startswith('back'))
        async def back_to_lesson_list(callback: CallbackQuery, state: FSMContext):

            # получаем id курса для отображения кнопок с уроками курса
            course_id = callback.data.split('_')[-1]
            await callback.message.edit_text(MESSAGES['LESSONS_LIST'])
            await callback.message.answer(
                MESSAGES['CHOOSE_LESSONS'],
                reply_markup=await self.kb.lessons_btn(course_id))

            # состояние на отлов выбора урока
            await state.set_state(LessonChooseState.lesson)

        @self.router.callback_query(F.data.startswith('start_test'), LessonChooseState.start_test)
        async def back_to_lesson_list(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()
            lesson = data['lesson']

            # получаем все тестовые вопросы по данному уроку и переворачиваем список, чтобы начиналось с №1
            self.test_questions = json.loads(lesson.questions)
            self.test_questions.reverse()

            user = await self.db.get_user_by_tg_id(callback.message.chat.id)

            # получаем актуальную попытку прохождения урока
            actual_lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            # создаем истории прохождения теста на урок
            await self.db.create_test_history(
                user_id=user.id,
                lesson_id=lesson.id,
                lesson_history_id=actual_lesson_history.id
            )

            # меняем статус прохождения урока на 'ТЕСТ'
            await self.db.mark_lesson_history_on_status_test(
                lesson_history_id=actual_lesson_history.id
            )

            first_question = self.test_questions.pop()
            await callback.message.answer(
                first_question['title'],
                reply_markup=await self.kb.test_answers_btn(first_question['questions'])
            )
            await state.set_state(LessonChooseState.test_answer)
            await state.update_data(answers=[])
            await state.update_data(lesson_history_id=actual_lesson_history.id)

        @self.router.callback_query(F.data.startswith('test_answer'), LessonChooseState.test_answer)
        async def save_test_answer(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()
            args = callback.data.split('/')
            answer = args[1]
            data['answers'].append(answer)

            try:
                question = self.test_questions.pop()
                await callback.message.edit_text(
                    question['title'],
                    reply_markup=await self.kb.test_answers_btn(question['questions'])
                )
                await state.set_state(LessonChooseState.test_answer)
            except IndexError:
                # когда вопросов больше не будет, то удаляем состояние, но данные оставляем()
                await state.set_state(state=None)

                # сохраняем ответы пользователя в БД
                await self.db.save_test_answers(
                    answers=data['answers'],
                    lesson_history_id=data['lesson_history_id']
                )

                # меняем статус на 'Пройден' у данной попытки прохождения теста
                await self.db.mark_lesson_history_on_status_done(
                    lesson_history_id=data['lesson_history_id']
                )

                await callback.message.edit_text(
                    'конец'
                )
                await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )


