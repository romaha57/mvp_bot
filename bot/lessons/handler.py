import asyncio
import json
from typing import Union

from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.filters import or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.courses.service import CourseService
from bot.handlers.base_handler import Handler
from bot.lessons.keyboards import LessonKeyboard
from bot.lessons.service import LessonService
from bot.lessons.states import LessonChooseState
from bot.settings.keyboards import BaseKeyboard
from bot.utils.answers import format_answers_text, send_user_answers_to_group
from bot.utils.delete_messages import delete_messages
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

        @self.router.callback_query(LessonChooseState.lesson, F.data.startswith('lesson'))
        async def choose_lesson(callback: CallbackQuery, state: FSMContext):
            # await state.clear()

            data = await state.get_data()

            lesson_name = callback.data.split('_')[1]
            lesson = await self.db.get_lesson_by_name(lesson_name)
            user = await self.db.get_user_by_tg_id(callback.message.chat.id)

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

            # удаляем сообщения со списком уроков
            await delete_messages(
                src=callback,
                data=data,
                state=state
            )

            # вывод информации об уроке
            if lesson:
                if lesson.video:
                    video_msg = await callback.message.answer_video(
                        lesson.video,
                        caption=lesson.title,
                        reply_markup=await self.kb.lesson_menu_btn(lesson)
                    )
                    video_description_msg = await callback.message.answer(
                        lesson.description
                    )

                    # сохраняем message_id, чтобы потом их удалить
                    await state.update_data(video_msg=video_msg.message_id)
                    await state.update_data(video_description_msg=video_description_msg.message_id)

                else:
                    msg1 = await callback.message.answer(lesson.title)
                    msg2 = await callback.message.answer(
                        lesson.description,
                        reply_markup=await self.kb.lesson_menu_btn(lesson)
                    )
                    # сохраняем message_id, чтобы потом их удалить
                    await state.update_data(msg1=msg1.message_id)
                    await state.update_data(msg2=msg2.message_id)

                # получаем актуальную попытку прохождения урока
                actual_lesson_history = await self.db.get_actual_lesson_history(
                    user_id=user.id,
                    lesson_id=lesson.id
                )
                await state.update_data(lesson_history_id=actual_lesson_history.id)
                await state.update_data(chat_id=callback.message.chat.id)

            else:
                await callback.message.answer(MESSAGES['NOT_FOUND_LESSON'])

            # состояние на прохождение теста после урока
            await state.set_state(LessonChooseState.start_task)
            await state.update_data(lesson=lesson)

        @self.router.callback_query(F.data.startswith('back'))
        async def back_to_lesson_list(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            # удаляем сообщения
            await delete_messages(
                src=callback,
                data=data,
                state=state
            )

            user = await self.db.get_user_by_tg_id(callback.message.chat.id)
            # получаем id курса для отображения кнопок с уроками курса
            course_id = callback.data.split('_')[-1]
            msg = await callback.message.answer(
                MESSAGES['CHOOSE_LESSONS'],
                reply_markup=await self.kb.lessons_btn(course_id, user.id))

            await callback.message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=await self.base_kb.menu_btn()
            )

            # состояние на отлов выбора урока
            await state.set_state(LessonChooseState.lesson)

            # сохраняем id сообщения для последующего удаления
            await state.update_data(delete_message_id=msg.message_id)
            await state.update_data(chat_id=callback.message.chat.id)

        @self.router.callback_query(F.data.startswith('start_task'), LessonChooseState.start_task)
        async def start_task_after_lesson(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            # удаляем предыдущие сообщения с кнопками
            await delete_messages(
                src=callback,
                data=data,
                state=state
            )

            lesson = data['lesson']

            # получаем тип задания к уроку
            task_type_id = await self.db.get_type_task_for_lesson(lesson)

            if task_type_id == 1:
                await close_lesson(src=callback, state=state)
            elif task_type_id == 2:
                await start_test_after_lesson(callback=callback, state=state)
            elif task_type_id == 3:
                await start_text_task_after_lesson(message=callback.message, state=state)
            elif task_type_id == 4:
                await start_image_task_after_lesson(message=callback.message, state=state)
            elif task_type_id == 5:
                await start_video_task_after_lesson(message=callback.message, state=state)
            elif task_type_id == 6:
                await start_file_task_after_lesson(message=callback.message, state=state)
            elif task_type_id == 7:
                await start_circle_task_after_lesson(message=callback.message, state=state)

        async def start_test_after_lesson(callback: CallbackQuery, state: FSMContext):
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

            msg = await callback.message.answer(
                text,
                reply_markup=await self.kb.test_answers_btn(count_questions)
            )
            await state.set_state(LessonChooseState.test_answer)

            await state.update_data(count_questions=count_questions)
            await state.update_data(question=first_question)
            await state.update_data(selected=[])
            await state.update_data(inline_message_id=str(callback.inline_message_id))
            await state.update_data(delete_test_message=msg.message_id)
            await state.update_data(chat_id=callback.message.chat.id)

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
        async def check_answer_on_quiz(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            if data['selected']:
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
                    await callback.message.answer(
                        MESSAGES['CORRECT_ANSWER'],
                        reply_markup=await self.kb.next_question_btn()
                    )

                else:
                    # получаем текст правильных ответов
                    answer = ''
                    for correct_answer_index in correct_answers:
                        answer += '\n' + question['questions'][correct_answer_index - 1]['title']

                    await callback.message.answer(
                        MESSAGES['INCORRECT_ANSWER'].format(
                            answer
                        ),
                        reply_markup=await self.kb.next_question_btn()
                    )

            else:
                await callback.message.answer(MESSAGES['NO_CHOOSE_ANSWER'])

        @self.router.callback_query(F.data.startswith('next_question'))
        async def next_question_in_test_after_lesson(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            # убираем историю выбранных пользователем ответов
            await state.update_data(selected=[])

            try:
                # получаем сообщение для удаления (удаляем предыдущий вопрос)

                # удаляем сообщения
                await delete_messages(
                    src=callback,
                    data=data,
                    state=state
                )

                # получаем следующий вопрос и записываем его в state
                question = self.test_questions.pop()
                await state.update_data(question=question)

                # формируем текст ответа и записываем кол-во вариантов ответа для формирования кнопок
                answers_text = await format_answers_text(question['questions'])
                text = f"{question['title']} \n {answers_text}"
                count_questions = len(question['questions'])

                msg = await callback.message.edit_text(
                    text,
                    reply_markup=await self.kb.test_answers_btn(count_questions))
                await state.update_data(delete_test_message=msg.message_id)
                await state.update_data(chat_id=callback.message.chat.id)

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
                    msg = await callback.message.edit_text(
                        MESSAGES['SUCCESS_TEST'].format(
                            user_percent_answer
                        ),
                        reply_markup=await self.kb.close_lesson_btn(data['lesson'])
                    )
                    await self.db.mark_lesson_history_on_status_done(data['lesson_history_id'])

                    # сохраняем msg_id чтобы потом удалить
                    await state.update_data(msg1=msg.message_id)

                else:
                    msg = await callback.message.edit_text(
                        MESSAGES['FAIL_TEST'],
                        reply_markup=await self.kb.start_again_lesson(data['lesson'])
                    )
                    await state.set_state(LessonChooseState.lesson)

                    # сохраняем msg_id чтобы потом удалить
                    await state.update_data(msg1=msg.message_id)

                    await self.db.mark_lesson_history_on_status_fail_test(data['lesson_history_id'])

                # обнуляем счетчик правильных ответов
                self.result_count = 0

                await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )

        @self.router.callback_query(F.data.startswith('close_lesson'))
        async def close_lesson(src: Union[CallbackQuery, Message], state: FSMContext):
            data = await state.get_data()

            # удаляем сообщения с кнопками
            await delete_messages(
                src=src,
                data=data,
                state=state
            )

            lesson = data['lesson']

            await self.db.mark_lesson_history_on_status_done(data['lesson_history_id'])
            next_lesson = await self.db.get_lesson_by_order_num(
                course_id=lesson.course_id,
                order_num=lesson.order_num + 1
            )

            # проверяем есть ли у данного урока доп задание
            additional_task = await self.db.get_additional_task_by_lesson(lesson)
            await state.update_data(additional_task=additional_task)

            # выводим доп задание с кнопками 'пропустить' и 'выполнил'
            if additional_task:

                # в зависимости от типа переменной берем id telegram
                if isinstance(src, CallbackQuery):
                    tg_id = src.message.chat.id
                else:
                    tg_id = src.from_user.id

                # создаем запись прохождения доп задания в БД
                additional_task_history = await self.db.create_additional_task_history(
                    tg_id=tg_id,
                    additional_task_id=additional_task.id,
                    lesson_history_id=data['lesson_history_id']
                )

                # сохраняем в состоянии id истории
                await state.update_data(additional_task_history_id=additional_task_history.id)

                await src.message.answer(
                    MESSAGES['ADDITIONAL_TASK'].format(
                        additional_task.title
                    )
                )
                additional_msg = await src.message.answer(
                    additional_task.description,
                    reply_markup=await self.kb.additional_task_btn()
                )

                await src.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )

                await state.update_data(additional_msg=additional_msg.message_id)

            # в зависимости от callback или message меняется отправка сообщения
            if isinstance(src, CallbackQuery):
                if next_lesson:
                    msg1 = await src.message.answer(
                        MESSAGES['NEXT_LESSON'],
                        reply_markup=await self.kb.next_lesson_btn(next_lesson)
                    )
                    await state.set_state(LessonChooseState.lesson)
                    await state.update_data(msg1=msg1.message_id)
                else:
                    await src.message.answer(
                        MESSAGES['ALL_LESSONS_DONE'],
                        reply_markup=await self.base_kb.menu_btn()
                    )
            else:
                if next_lesson:
                    msg1 = await src.answer(
                        MESSAGES['NEXT_LESSON'],
                        reply_markup=await self.kb.next_lesson_btn(next_lesson)
                    )
                    await state.set_state(LessonChooseState.lesson)
                    await state.update_data(msg1=msg1.message_id)
                else:
                    await src.answer(
                        MESSAGES['ALL_LESSONS_DONE'],
                        reply_markup=await self.base_kb.menu_btn()
                    )

        async def start_text_task_after_lesson(message: Message, state: FSMContext):
            data = await state.get_data()

            lesson_work_description = data['lesson'].work_description

            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.test_answer)

        @self.router.message(LessonChooseState.test_answer)
        async def get_text_answer(message: Message, state: FSMContext):
            data = await state.get_data()
            lesson = data['lesson']

            if message.content_type == ContentType.TEXT:
                await self.db.save_user_answer(
                    answer=message.text,
                    lesson_history_id=data['lesson_history_id']
                )
                await message.answer(MESSAGES['YOUR_ANSWER_SAVE'])
                await close_lesson(src=message, state=state)

                # отправляем отчет в группу курса
                await send_user_answers_to_group(
                    bot=message.bot,
                    course_id=lesson.course_id,
                    name=message.from_user.full_name,
                    lesson_name=lesson.title,
                    homework=lesson.work_description
                )
            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        async def start_image_task_after_lesson(message: Message, state: FSMContext):
            data = await state.get_data()

            lesson_work_description = data['lesson'].work_description
            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.image_answer)

        @self.router.message(LessonChooseState.image_answer)
        async def get_image_answer(message: Message, state: FSMContext):

            data = await state.get_data()
            lesson = data['lesson']

            if message.content_type == ContentType.PHOTO:
                answer = message.photo[-1].file_id
                await self.db.save_user_answer(
                    answer=answer,
                    lesson_history_id=data['lesson_history_id']
                )
                await message.answer(MESSAGES['YOUR_ANSWER_SAVE'])
                await close_lesson(src=message, state=state)

                # отправляем отчет в группу курса
                await send_user_answers_to_group(
                    bot=message.bot,
                    course_id=lesson.course_id,
                    name=message.from_user.full_name,
                    lesson_name=lesson.title,
                    homework=lesson.work_description
                )

            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        async def start_video_task_after_lesson(message: Message, state: FSMContext):
            data = await state.get_data()

            lesson_work_description = data['lesson'].work_description
            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.video_answer)

        @self.router.message(LessonChooseState.video_answer)
        async def get_video_answer(message: Message, state: FSMContext):

            data = await state.get_data()
            lesson = data['lesson']

            if message.content_type == ContentType.VIDEO:
                answer = message.video.file_id
                await self.db.save_user_answer(
                    answer=answer,
                    lesson_history_id=data['lesson_history_id']
                )
                await message.answer(MESSAGES['YOUR_ANSWER_SAVE'])
                await close_lesson(src=message, state=state)

                # отправляем отчет в группу курса
                await send_user_answers_to_group(
                    bot=message.bot,
                    course_id=lesson.course_id,
                    name=message.from_user.full_name,
                    lesson_name=lesson.title,
                    homework=lesson.work_description
                )

            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        async def start_file_task_after_lesson(message: Message, state: FSMContext):
            data = await state.get_data()

            lesson_work_description = data['lesson'].work_description
            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.file_answer)

        @self.router.message(LessonChooseState.file_answer)
        async def get_file_answer(message: Message, state: FSMContext):

            data = await state.get_data()
            lesson = data['lesson']

            if message.content_type == ContentType.DOCUMENT:
                answer = message.document.file_id
                await self.db.save_user_answer(
                    answer=answer,
                    lesson_history_id=data['lesson_history_id']
                )
                await message.answer(MESSAGES['YOUR_ANSWER_SAVE'])
                await close_lesson(src=message, state=state)

                # отправляем отчет в группу курса
                await send_user_answers_to_group(
                    bot=message.bot,
                    course_id=lesson.course_id,
                    name=message.from_user.full_name,
                    lesson_name=lesson.title,
                    homework=lesson.work_description
                )

            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        async def start_circle_task_after_lesson(message: Message, state: FSMContext):
            data = await state.get_data()

            lesson_work_description = data['lesson'].work_description
            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.circle_answer)

        @self.router.message(LessonChooseState.circle_answer)
        async def get_circle_answer(message: Message, state: FSMContext):

            data = await state.get_data()
            lesson = data['lesson']

            if message.content_type == ContentType.VIDEO_NOTE:
                answer = message.video_note.file_id
                await self.db.save_user_answer(
                    answer=answer,
                    lesson_history_id=data['lesson_history_id']
                )
                await message.answer(MESSAGES['YOUR_ANSWER_SAVE'])
                await close_lesson(src=message, state=state)

                # отправляем отчет в группу курса
                await send_user_answers_to_group(
                    bot=message.bot,
                    course_id=lesson.course_id,
                    name=message.from_user.full_name,
                    lesson_name=lesson.title,
                    homework=lesson.work_description
                )

            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        @self.router.callback_query(LessonChooseState.lesson, F.data.startswith('skip_additional_task'))
        async def skip_additional_task(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            # если пользователь нажал 'Пропустить', то удаляем это сообщение с кнопками
            if data.get('additional_msg'):
                await callback.bot.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('additional_msg')
                )

                await state.update_data(additional_msg=None)

        @self.router.callback_query(LessonChooseState.lesson, F.data.startswith('done_additional_task'))
        async def done_additional_task(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            await delete_messages(
                data=data,
                state=state,
                src=callback
            )
            additional_task = data.get('additional_task')

            # если задание не нужно проверять, то начисляем сразу бонусы
            if not additional_task.checkup:

                # меняем статус прохождения доп задания на 'Сделан'
                await self.db.mark_additional_task_done_status(
                    additional_task_history_id=data['additional_task_history_id']
                )

                # зачисляем бонусы на аккаунт
                await self.db.add_reward_to_user(
                    tg_id=callback.message.chat.id,
                    reward=additional_task.reward,
                    comment=f'Начислено за доп задание: {additional_task.title}'
                )

                await callback.message.answer(
                    MESSAGES['REWARDS_WAS_ADDED']
                )
            else:
                # меняем статус прохождения доп задания на 'Ожидает проверки'
                await self.db.mark_additional_task_await_review_status(
                    additional_task_history_id=data['additional_task_history_id']
                )

                await callback.message.answer(
                    MESSAGES['ADD_REWARD_AFTER_TIME']
                )

            # получаем следующий урок 
            lesson = data['lesson']

            await self.db.mark_lesson_history_on_status_done(data['lesson_history_id'])
            next_lesson = await self.db.get_lesson_by_order_num(
                course_id=lesson.course_id,
                order_num=lesson.order_num + 1
            )
            if next_lesson:
                msg1 = await callback.message.answer(
                    MESSAGES['NEXT_LESSON'],
                    reply_markup=await self.kb.next_lesson_btn(next_lesson)
                )
                await state.set_state(LessonChooseState.lesson)
                await state.update_data(msg1=msg1.message_id)

            else:
                await callback.message.answer(
                    MESSAGES['ALL_LESSONS_DONE'],
                    reply_markup=await self.base_kb.menu_btn()
                )
