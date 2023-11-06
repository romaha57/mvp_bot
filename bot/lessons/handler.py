import json

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import or_f

from bot.courses.service import CourseService
from bot.handlers.base_handler import Handler
from bot.lessons.keyboards import LessonKeyboard
from bot.lessons.service import LessonService
from bot.lessons.states import LessonChooseState
from bot.settings.keyboards import BaseKeyboard
from bot.utils.answers import format_answers_text
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
        self.result_count = 0

    def handle(self):

        @self.router.message(LessonChooseState.lesson, F.text)
        async def choose_lesson(message: Message, state: FSMContext):
            await state.clear()
            print(message.text)
            lesson = await self.db.get_lesson_by_name(message.text)
            user = await self.db.get_user_by_tg_id(message.from_user.id)
            print(lesson)
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

            # вывод информации об уроке
            if lesson:
                if lesson.video:
                    await message.answer_video(
                        lesson.video,
                        caption=lesson.title
                    )
                    await message.answer(
                        lesson.description,
                        reply_markup=await self.kb.lesson_menu_btn(lesson)
                    )

                else:
                    await message.answer(lesson.title)
                    await message.answer(
                        lesson.description,
                        reply_markup=await self.kb.lesson_menu_btn(lesson)
                    )

                # получаем актуальную попытку прохождения урока
                actual_lesson_history = await self.db.get_actual_lesson_history(
                    user_id=user.id,
                    lesson_id=lesson.id
                )
                await state.update_data(lesson_history_id=actual_lesson_history.id)

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

            # сохранить общее количество вопросов
            await state.update_data(questions_count=len(self.test_questions))

            user = await self.db.get_user_by_tg_id(callback.message.chat.id)


            # создаем истории прохождения теста на урок
            await self.db.create_test_history(
                user_id=user.id,
                lesson_id=lesson.id,
                lesson_history_id=data['lesson_history_id']
            )

            # меняем статус прохождения урока на 'ТЕСТ'
            await self.db.mark_lesson_history_on_status_test(
                lesson_history_id=data['lesson_history_id']
            )

            # берем первый вопрос, формируем сообщение с вопросом и вариантами ответа
            # и записываем количество вариантов ответа для формирования кнопок с выбором
            first_question = self.test_questions.pop()
            answers_text = await format_answers_text(first_question['questions'])
            text = f"{first_question['title']} \n {answers_text}"
            count_questions = len(first_question['questions'])

            await callback.message.answer(
                text,
                reply_markup=await self.kb.test_answers_btn(count_questions)
            )
            await state.set_state(LessonChooseState.test_answer)
            await state.update_data(count_questions=count_questions)
            await state.update_data(question=first_question)
            await state.update_data(selected=[])
            await state.update_data(inline_message_id=str(callback.inline_message_id))


        @self.router.callback_query(F.data.startswith('test_answer'), LessonChooseState.test_answer)
        async def save_test_answer(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            # получаем выбранный вариант пользователя
            selected = int(callback.data.split('_')[-1])
            count_questions = len(data['question']['questions'])

            # логика по отметке выбранных ответов(добавляем в список выбранные или убираем из него, если такой уж есть)
            if selected in data['selected']:
                data['selected'].remove(selected)
            else:
                data['selected'].append(selected)

            await callback.message.edit_reply_markup(
                data['inline_message_id'],
                reply_markup=await self.kb.test_answers_btn(count_questions, selected=data['selected'])
            )

        @self.router.callback_query(F.data.startswith('check_answer'))
        async def close_lesson(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            # получаем все выбранные пользователям ответы и сортируем по возрастанию цифр
            data['selected'].sort()
            selected = data['selected']

            # получаем вопрос на который отвечал пользователь
            question = data['question']
            correct_answers = []

            # получаем все правильные ответы на этот вопрос и сверяем с выбранными пользователем
            for index, answer in enumerate(question['questions'], 1):
                if answer['good']:
                    correct_answers.append(index)

            if correct_answers == selected:
                self.result_count += 1
                await callback.message.answer('все верно',
                                              reply_markup=await self.kb.next_question_btn())

            else:
                await callback.message.answer('ошибка', reply_markup=await self.kb.next_question_btn())

        @self.router.callback_query(F.data.startswith('next_question'))
        async def close_lesson(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            # убираем историю выбранных пользователем ответов
            await state.update_data(selected=[])

            try:
                # получаем следующий вопрос и записываем его в state
                question = self.test_questions.pop()
                await state.update_data(question=question)

                # формируем текст ответа и записываем кол-во вариантов ответа для формирования кнопок
                answers_text = await format_answers_text(question['questions'])
                text = f"{question['title']} \n {answers_text}"
                count_questions = len(question['questions'])

                await callback.message.edit_text(
                    text,
                    reply_markup=await self.kb.test_answers_btn(count_questions))

                await state.set_state(LessonChooseState.test_answer)
            except IndexError:
                # когда вопросов больше не будет, то удаляем состояние, но данные оставляем
                await state.set_state(state=None)

                # меняем статус на 'Пройден' у данной попытки прохождения теста
                await self.db.mark_lesson_history_on_status_done(
                    lesson_history_id=data['lesson_history_id']
                )

                # вывод результат теста с подсчетом % правильных
                user_percent_answer = int((self.result_count / data['questions_count']) * 100)

                # если пользователь набрал нужный % прохождения
                if user_percent_answer > data['lesson'].questions_percent:

                    await callback.message.edit_text(
                        MESSAGES['SUCCESS_TEST'].format(
                            user_percent_answer
                        )
                    )
                    await self.db.mark_lesson_history_on_status_done(data['lesson_history_id'])

                else:
                    await callback.message.edit_text(
                        MESSAGES['FAIL_TEST']
                    )
                    await self.db.mark_lesson_history_on_status_fail_test(data['lesson_history_id'])

                # обнуляем счетчик правильных ответов
                self.result_count = 0

                await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )

        @self.router.callback_query(F.data.startswith('close_lesson'))
        async def close_lesson(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()
            await self.db.mark_lesson_history_on_status_done(data['lesson_history_id'])
            next_lesson = await self.db.get_lesson_by_order_num(
                course_id=data['lesson'].course_id,
                order_num=data['lesson'].order_num + 1
            )
            if next_lesson:
                await callback.message.answer(
                    MESSAGES['NEXT_LESSON'],
                    reply_markup=await self.kb.next_lesson_btn(next_lesson)
                )
                await state.set_state(LessonChooseState.lesson)
            else:
                await callback.message.answer(
                    MESSAGES['ALL_LESSONS_DONE'],
                    reply_markup=await self.base_kb.menu_btn()
                )




