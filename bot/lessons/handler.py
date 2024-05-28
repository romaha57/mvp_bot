import datetime
import json
import traceback
from typing import Union

from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from loguru import logger

from bot.courses.service import CourseService
from bot.handlers.base_handler import Handler
from bot.lessons.keyboards import LessonKeyboard
from bot.lessons.service import LessonService
from bot.lessons.states import Certificate, LessonChooseState
from bot.settings.keyboards import BaseKeyboard
from bot.test_promocode.keyboards import TestPromoKeyboard
from bot.test_promocode.utils import is_valid_test_promo
from bot.users.service import UserService
from bot.utils.answers import (format_answers_text, get_images_by_place,
                               send_user_answers_to_group, show_lesson_info, send_image, catch_menu_btn_in_answers)
from bot.utils.buttons import BUTTONS
from bot.utils.certificate import build_certificate
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class LessonHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = LessonService()
        self.course_db = CourseService()
        self.user_db = UserService()
        self.kb = LessonKeyboard()
        self.base_kb = BaseKeyboard()
        self.test_promo_kb = TestPromoKeyboard()
        self.test_questions = None
        self.result_count = 0
        self.emoji_list = None

    def handle(self):

        @self.router.callback_query(LessonChooseState.lesson, F.data.startswith('lesson'))
        async def choose_lesson(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                await callback.message.answer(
                    MESSAGES['YOUR_PROMOCODE_IS_EXPIRED'],
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

                lesson_id = callback.data.split('_')[1]
                lesson = await self.db.get_lesson_by_id(lesson_id)

                user = await self.db.get_user_by_tg_id(callback.message.chat.id)
                logger.debug(f'Пользователь: {callback.message.chat.id} выбрал lesson: id-{lesson.id}/{lesson.title}')

                course_history = await self.course_db.get_or_create_history(
                    course_id=lesson.course_id,
                    user=user
                )

                await delete_messages(
                    src=callback.message,
                    data=data,
                    state=state
                )

                if lesson:
                    await self.db.create_history(
                        lesson_id=lesson.id,
                        user_id=user.id,
                        course_history_id=course_history.id
                    )

                    await show_lesson_info(
                        message=callback.message,
                        state=state,
                        self=self,
                        lesson=lesson,
                        user_id=user.id
                    )

                else:
                    promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
                    courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                    await callback.message.answer(
                        MESSAGES['NOT_FOUND_LESSON'],
                        reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                    )

                # состояние на прохождение теста после урока
                await state.set_state(LessonChooseState.start_task)

                await state.update_data(lesson=lesson)
                await state.update_data(lesson_id=lesson.id)

        @self.router.callback_query(F.data.startswith('back'))
        async def back_to_lesson_list(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            # удаляем сообщения
            await delete_messages(
                src=callback.message,
                data=data,
                state=state
            )

            user = await self.db.get_user_by_tg_id(callback.message.chat.id)
            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                await callback.message.answer(
                    MESSAGES['YOUR_PROMOCODE_IS_EXPIRED'],
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

                course_id = callback.data.split('_')[-1]
                msg = await callback.message.answer(
                    MESSAGES['CHOOSE_LESSONS'],
                    reply_markup=await self.kb.lessons_btn(course_id, user.id, promocode))

                await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )

                await state.set_state(LessonChooseState.lesson)
                await state.update_data(msg=msg.message_id)

        @self.router.callback_query(F.data.startswith('start_task'))
        async def start_task_after_lesson(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            # удаляем предыдущие сообщения с кнопками
            await delete_messages(
                src=callback.message,
                data=data,
                state=state
            )

            lesson = data.get('lesson')
            # отправка доп. изображений к уроку
            await send_image(
                lesson=lesson,
                message=callback.message,
                place='before_work'
            )

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

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            lesson = data.get('lesson')
            user = await self.db.get_user_by_tg_id(callback.message.chat.id)
            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            # получаем все тестовые вопросы по данному уроку и переворачиваем список, чтобы начиналось с №1
            self.test_questions = json.loads(lesson.questions)
            self.test_questions.reverse()

            # меняем статус прохождения урока на 'ТЕСТ'
            await self.db.mark_lesson_history_on_status_test(
                lesson_history_id=lesson_history.id
            )

            # берем первый вопрос, формируем сообщение с вопросом и вариантами ответа
            # и записываем количество вариантов ответа для формирования кнопок с выбором
            first_question = self.test_questions.pop()
            answers_text = await format_answers_text(first_question['questions'])
            text = f"{first_question['title']} \n\n{answers_text}"
            count_questions = len(first_question['questions'])

            msg = await callback.message.answer(
                text,
                reply_markup=await self.kb.test_answers_btn(count_questions)
            )
            await state.set_state(LessonChooseState.test_answer)

            await callback.message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=await self.base_kb.menu_btn()
            )

            await state.update_data(count_questions=count_questions)
            await state.update_data(question=first_question)
            await state.update_data(selected=[])
            await state.update_data(inline_message_id=str(callback.inline_message_id))
            await state.update_data(delete_test_message=msg.message_id)

        @self.router.callback_query(F.data.startswith('test_answer'), LessonChooseState.test_answer)
        async def save_test_answer(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            # получаем выбранный вариант пользователя
            selected = int(callback.data.split('_')[-1])
            count_questions = len(data['question']['questions'])

            # логика по отметке выбранных ответов(добавляем в список выбранные или убираем из него, если такой уж есть)
            if selected in data['selected']:
                data['selected'].remove(selected)
            else:
                data['selected'].append(selected)

            await state.update_data(selected=data['selected'])

            await callback.message.edit_reply_markup(
                data['inline_message_id'],
                reply_markup=await self.kb.test_answers_btn(count_questions, selected=data['selected'])
            )

        @self.router.callback_query(F.data.startswith('check_answer'))
        async def check_answer_on_test_lesson(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            lesson = data.get('lesson')
            user = await self.db.get_user_by_tg_id(callback.message.chat.id)
            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            if data['selected']:
                await delete_messages(
                    data=data,
                    state=state,
                    src=callback.message
                )
                # получаем все выбранные пользователям ответы и сортируем по возрастанию цифр
                data['selected'].sort()
                users_answers = data.get('users_answers')
                # добавляем в список ответов пользователя, выбранный им ответ
                users_answers.extend(data['selected'])
                selected = data.get('selected')

                # получаем вопрос на который отвечал пользователь
                question = data.get('question')
                correct_answers = []

                # получаем все правильные ответы на этот вопрос и сверяем с выбранными пользователем
                for index, answer in enumerate(question['questions'], 1):
                    if answer['good']:
                        correct_answers.append(index)

                if correct_answers == selected:
                    self.result_count += 1
                    msg = await callback.message.answer(
                        MESSAGES['CORRECT_ANSWER'],
                        reply_markup=await self.kb.next_question_btn(self.test_questions)
                    )
                    await state.update_data(msg=msg.message_id)
                else:
                    letter_list = ['1', 'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И']
                    # получаем текст правильных ответов
                    answer = ''
                    for correct_answer_index in correct_answers:
                        answer += f'\n{letter_list[correct_answer_index]}. ' + \
                                  question['questions'][correct_answer_index - 1]['title']
                    await callback.message.answer(
                        MESSAGES['INCORRECT_ANSWER'].format(
                            answer
                        ),
                        reply_markup=await self.kb.next_question_btn(self.test_questions)
                    )

                # создаем истории прохождения теста на урок
                questions = json.loads(lesson.questions)
                user_answer = str([i - 1 for i in selected])
                await self.db.create_test_history(
                    user_id=user.id,
                    lesson_id=lesson.id,
                    lesson_history_id=lesson_history.id,
                    question_id=questions.index(question),
                    answers=user_answer
                )

            else:
                await callback.answer(MESSAGES['NO_CHOOSE_ANSWER'], show_alert=True)

        @self.router.callback_query(F.data.startswith('next_question'))
        async def next_question_in_test_after_lesson(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            # убираем историю выбранных пользователем ответов
            await state.update_data(selected=[])
            user = await self.user_db.get_user_by_tg_id(callback.message.chat.id)
            lesson = data.get('lesson')
            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            try:
                # await delete_messages(
                #     src=callback.message,
                #     data=data,
                #     state=state
                # )

                # получаем следующий вопрос и записываем его в state
                question = self.test_questions.pop()
                await state.update_data(question=question)

                # формируем текст ответа и записываем кол-во вариантов ответа для формирования кнопок
                answers_text = await format_answers_text(question['questions'])
                text = f"{question['title']} \n\n{answers_text}"
                count_questions = len(question['questions'])

                msg = await callback.message.edit_text(
                    text,
                    reply_markup=await self.kb.test_answers_btn(count_questions))

                menu_msg = await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )

                await state.update_data(delete_test_message=msg.message_id)
                await state.update_data(msg=menu_msg.message_id)
                await state.set_state(LessonChooseState.test_answer)

            except IndexError:
                await state.set_state(state=None)

                total_questions = len(json.loads(lesson.questions))
                # вывод результат теста с подсчетом % правильных
                user_percent_answer = int((self.result_count / total_questions) * 100)
                logger.debug(
                    f'Юзер: {callback.message.chat.id} ответил верно на {self.result_count} из {total_questions}'
                )

                # преобразовываем ответы пользователя из цифр в буквы
                letter_list = ['1', 'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И']
                answer = [letter_list[i] for i in data['users_answers']]
                answer = str(answer)

                # если пользователь набрал нужный % прохождения
                if user_percent_answer >= lesson.questions_percent:
                    await callback.message.edit_text(
                        MESSAGES['SUCCESS_TEST'].format(
                            user_percent_answer
                        ),
                    )
                    await self.db.mark_lesson_history_on_status_done(lesson_history.id)
                    test_lesson_history_id = await self.db.get_actual_test_lesson_history(
                        user_id=user.id,
                        lesson_id=lesson.id
                    )
                    await self.db.mark_test_lesson_history_on_status_done(test_lesson_history_id)

                    # обнуляем счетчик правильных ответов
                    self.result_count = 0

                    await close_lesson(
                        src=callback,
                        state=state
                    )

                else:
                    msg = await callback.message.edit_text(
                        MESSAGES['FAIL_TEST'].format(
                            user_percent_answer,
                            lesson.questions_percent
                        ),
                        reply_markup=await self.kb.start_again_lesson(lesson)
                    )
                    await state.set_state(LessonChooseState.lesson)

                    # сохраняем msg_id чтобы потом удалить
                    await state.update_data(msg1=msg.message_id)

                    await self.db.mark_lesson_history_on_status_fail_test(lesson_history.id)

                    # обнуляем счетчик правильных ответов
                    self.result_count = 0

        @self.router.callback_query(F.data.startswith('close_lesson'))
        async def close_lesson(src: Union[CallbackQuery, Message], state: FSMContext):

            # в зависимости от callback или message меняется отправка сообщения
            if isinstance(src, CallbackQuery):
                src = src.message

            await state.update_data(chat_id=src.chat.id)

            data = await state.get_data()

            # удаляем сообщения с кнопками
            await delete_messages(
                src=src,
                data=data,
                state=state
            )
            user = await self.user_db.get_user_by_tg_id(src.chat.id)
            promocode = await self.db.get_promocode_by_tg_id(src.chat.id)
            lesson = data.get('lesson')
            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            await self.db.mark_lesson_history_on_status_done(lesson_history.id)
            next_lesson = await self.db.get_lesson_by_order_num(
                course_id=lesson.course_id,
                order_num=lesson.order_num + 1
            )

            # проверяем есть ли у данного урока доп задание
            additional_task = await self.db.get_additional_task_by_lesson(lesson)

            logger.debug(
                f"Пользователь {src.chat.id}, в close_lesson")

            await send_image(
                lesson=lesson,
                message=src,
                place='after_work'
            )

            if additional_task:
                logger.debug(f"additional_task user_id: {user.id} - {user.username}")
                # создаем запись прохождения доп задания в БД
                await self.db.create_additional_task_history(
                    user_id=user.id,
                    additional_task_id=additional_task.id,
                    lesson_history_id=lesson_history.id
                )

                msg = await src.answer(
                    additional_task.description,
                    reply_markup=await self.kb.additional_task_btn()
                )

                await state.update_data(additional_msg=msg.message_id)

            if next_lesson:
                if (promocode.is_test and next_lesson.order_num > promocode.lesson_cnt) or \
                        (promocode.is_test and not is_valid_test_promo(user)):

                    await src.answer(
                        MESSAGES['END_TEST_PERIOD'],
                        reply_markup=await self.test_promo_kb.test_promo_menu()
                    )
                    await state.set_state(state=None)

                else:
                    msg1 = await src.answer(
                        MESSAGES['NEXT_LESSON'],
                        reply_markup=await self.kb.next_lesson_btn(next_lesson)
                    )
                    await state.set_state(LessonChooseState.lesson)
                    await state.update_data(msg1=msg1.message_id)

                await src.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )

            else:
                # отмечаем курс как 'Пройден'
                course_history_id = await self.course_db.get_course_history_id_by_lesson_history(lesson_history.id)
                await self.course_db.mark_course_done(course_history_id)

                course_id = lesson.course_id
                course = await self.course_db.get_course_by_id(course_id)
                await state.update_data(course_id=course_id)
                await src.answer(
                    course.outro,
                    reply_markup=await self.base_kb.menu_btn()
                )

                try:
                    if course.outro_video:
                        await src.answer_video(
                            video=course.outro_video
                        )
                except TelegramBadRequest as e:
                    if 'VOICE_MESSAGES_FORBIDDEN' in e.message:
                        await src.answer(
                            MESSAGES['VIDEO_ERROR_FORBIDDEN']
                        )
                    else:
                        await src.answer(
                            MESSAGES['VIDEO_ERROR']
                        )
                        logger.warning(f'Не удалось отправить видео {src.chat.id} -- {e.message}')

                if course.certificate_img:
                    await src.answer(
                        MESSAGES['ADD_YOUR_FULLNAME']
                    )
                    await state.set_state(Certificate.fullname)

                else:
                    await src.answer(
                        MESSAGES['ALL_LESSONS_DONE'],
                        reply_markup=await self.base_kb.menu_btn())

        @self.router.message(Certificate.fullname)
        async def catch_fullname_for_certificate(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            course_id = data.get('course_id')
            course = await self.course_db.get_course_by_id(course_id)

            fio = message.text

            if fio != BUTTONS['MENU']:
                if course.certificate_img:
                    # собираем сертификат для текущего пользователя
                    await message.answer(
                        MESSAGES['CERTIFICATE']
                    )

                    # формируем сертификат
                    build_certificate(
                        user_id=message.chat.id,
                        fullname=fio,
                        course_name=course.title
                    )
                    # читаем файл и отправляем пользователю
                    file_path = f'/app/static/certificate_{message.chat.id}.pdf'
                    certificate = FSInputFile(file_path)
                    logger.debug(f'Пользователь: {message.chat.id} get certificate {certificate} on path: {file_path}')
                    await message.bot.send_document(
                        chat_id=data['chat_id'],
                        document=certificate
                    )

                    await self.user_db.save_fullname(
                        fullname=fio,
                        tg_id=message.from_user.id
                    )

                    await message.answer(
                        MESSAGES['GO_TO_MENU'],
                        reply_markup=await self.base_kb.menu_btn()
                    )

                    await state.set_state(state=None)

            else:
                await catch_menu_btn_in_answers(
                    self=self,
                    state=state,
                    message=message,
                    tg_id=message.chat.id
                )


        async def start_text_task_after_lesson(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            lesson_id = data.get('lesson_id')
            lesson = await self.db.get_lesson_by_id(lesson_id)
            lesson_work_description = lesson.work_description

            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.text_answer)

        @self.router.message(LessonChooseState.text_answer)
        async def get_text_answer(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            user = await self.user_db.get_user_by_tg_id(message.chat.id)
            lesson = data.get('lesson')
            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            if message.content_type == ContentType.TEXT and message.text != BUTTONS['MENU']:
                await state.set_state(state=None)
                await self.db.save_user_answer(
                    answer=message.text,
                    lesson_history_id=lesson_history.id
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

            elif message.text == BUTTONS['MENU']:
                await catch_menu_btn_in_answers(
                    self=self,
                    state=state,
                    message=message,
                    tg_id=message.chat.id
                )

            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        async def start_image_task_after_lesson(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            lesson = data.get('lesson')
            lesson_work_description = lesson.work_description

            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.image_answer)

        @self.router.message(LessonChooseState.image_answer)
        async def get_image_answer(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            user = await self.user_db.get_user_by_tg_id(message.chat.id)
            lesson = data.get('lesson')
            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            if message.content_type == ContentType.PHOTO:
                await state.set_state(state=None)
                answer = message.photo[-1].file_id
                await self.db.save_user_answer(
                    answer=answer,
                    lesson_history_id=lesson_history.id
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

            elif message.text == BUTTONS['MENU']:
                await catch_menu_btn_in_answers(
                    self=self,
                    state=state,
                    message=message,
                    tg_id=message.chat.id
                )

            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        async def start_video_task_after_lesson(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            lesson = data.get('lesson')
            lesson_work_description = lesson.work_description

            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.video_answer)

        @self.router.message(LessonChooseState.video_answer)
        async def get_video_answer(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            user = await self.user_db.get_user_by_tg_id(message.chat.id)
            lesson = data.get('lesson')
            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            if message.content_type == ContentType.VIDEO:
                await state.set_state(state=None)
                answer = message.video.file_id
                await self.db.save_user_answer(
                    answer=answer,
                    lesson_history_id=lesson_history.id
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

            elif message.text == BUTTONS['MENU']:
                await catch_menu_btn_in_answers(
                    self=self,
                    state=state,
                    message=message,
                    tg_id=message.chat.id
                )

            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        async def start_file_task_after_lesson(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            lesson = data.get('lesson')
            lesson_work_description = lesson.work_description

            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.file_answer)

        @self.router.message(LessonChooseState.file_answer)
        async def get_file_answer(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            user = await self.user_db.get_user_by_tg_id(message.chat.id)
            lesson = data.get('lesson')
            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            if message.content_type == ContentType.DOCUMENT:
                await state.set_state(state=None)
                answer = message.document.file_id
                await self.db.save_user_answer(
                    answer=answer,
                    lesson_history_id=lesson_history.id
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

            elif message.text == BUTTONS['MENU']:
                await catch_menu_btn_in_answers(
                    self=self,
                    state=state,
                    message=message,
                    tg_id=message.chat.id
                )

            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        async def start_circle_task_after_lesson(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            lesson = data.get('lesson')
            lesson_work_description = lesson.work_description

            # получаем текст вопроса и выводим его, и затем отлавливаем ответ пользователя
            await message.answer(lesson_work_description)
            await state.set_state(LessonChooseState.circle_answer)

        @self.router.message(LessonChooseState.circle_answer)
        async def get_circle_answer(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            user = await self.user_db.get_user_by_tg_id(message.chat.id)
            lesson = data.get('lesson')
            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            if message.content_type == ContentType.VIDEO_NOTE:
                await state.set_state(state=None)

                answer = message.video_note.file_id
                await self.db.save_user_answer(
                    answer=answer,
                    lesson_history_id=lesson_history.id
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

            elif message.text == BUTTONS['MENU']:
                await catch_menu_btn_in_answers(
                    self=self,
                    state=state,
                    message=message,
                    tg_id=message.chat.id
                )

            else:
                await message.answer(MESSAGES['PLEASE_WRITE_CORRECT_ANSWER'])

        @self.router.callback_query(LessonChooseState.lesson, F.data.startswith('skip_additional_task'))
        async def skip_additional_task(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            await delete_messages(
                data=data,
                state=state,
                src=callback.message
            )

        @self.router.callback_query(LessonChooseState.lesson, F.data.startswith('done_additional_task'))
        async def done_additional_task(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            await delete_messages(
                data=data,
                state=state,
                src=callback.message
            )
            user = await self.user_db.get_user_by_tg_id(callback.message.chat.id)
            lesson = data.get('lesson')
            additional_task = await self.db.get_additional_task_by_lesson(lesson)
            additional_task_history_id = await self.db.get_additional_task_history(
                tg_id=callback.message.chat.id,
                additional_task_id=additional_task.id,

            )

            # если задание не нужно проверять, то начисляем сразу бонусы
            if not additional_task.checkup:

                # меняем статус прохождения доп задания на 'Сделан'
                await self.db.mark_additional_task_done_status(
                    additional_task_history_id=additional_task_history_id
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
                    additional_task_history_id=additional_task_history_id
                )

                await callback.message.answer(
                    MESSAGES['ADD_REWARD_AFTER_TIME']
                )

            lesson_history = await self.db.get_actual_lesson_history(
                user_id=user.id,
                lesson_id=lesson.id
            )

            await self.db.mark_lesson_history_on_status_done(lesson_history.id)
            next_lesson = await self.db.get_lesson_by_order_num(
                course_id=lesson.course_id,
                order_num=lesson.order_num + 1
            )
            if next_lesson:
                msg = await callback.message.answer(
                    MESSAGES['NEXT_LESSON'],
                    reply_markup=await self.kb.next_lesson_btn(next_lesson)
                )
                await state.set_state(LessonChooseState.lesson)
                await state.update_data(msg=msg.message_id)

            else:
                course = await self.course_db.get_course_by_id(lesson.course_id)
                await callback.message.answer(
                    course.outro,
                    reply_markup=await self.base_kb.menu_btn()
                )

        @self.router.callback_query(F.data.startswith('emoji'))
        async def increment_emoji_count(callback: CallbackQuery, state: FSMContext):
            """Отлавливаем нажатие на кнопку по смайликом"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            emoji_from_user = callback.data.split('_')[-1]

            lesson = data.get('lesson')

            lessons_ratings = lesson.buttons_rates
            if lessons_ratings:
                lessons_ratings = json.loads(lessons_ratings)

                # ---------------------Логика добавления оценки к уроку --------------------------

                for rate in lessons_ratings:
                    if rate['button'] == emoji_from_user:
                        rate['count'] += 1

                lessons_ratings_str = json.dumps(lessons_ratings, ensure_ascii=False)
                await self.db.increment_emoji_count(lesson, lessons_ratings_str)
                # ----------------------------------- КОНЕЦ --------------------------------------

                try:
                    if data.get('msg_edit'):
                        await callback.bot.edit_message_reply_markup(
                            chat_id=data['chat_id'],
                            message_id=data['msg_edit'],
                            reply_markup=await self.kb.lesson_menu_btn(lesson, lessons_ratings)
                        )
                except TelegramBadRequest:
                    pass
