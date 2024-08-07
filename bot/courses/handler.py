import datetime
import pprint
import random
import traceback

from aiogram import Bot, F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from loguru import logger

from bot.courses.keyboards import CourseKeyboard
from bot.courses.service import CourseService
from bot.courses.states import CourseChooseState
from bot.handlers.base_handler import Handler
from bot.lessons.keyboards import LessonKeyboard
from bot.lessons.models import Lessons
from bot.lessons.service import LessonService
from bot.lessons.states import LessonChooseState
from bot.settings.keyboards import BaseKeyboard
from bot.users.service import UserService
from bot.utils.answers import show_lesson_info, show_course_intro_first_time, add_course_without_history
from bot.utils.buttons import BUTTONS
from bot.utils.certificate import build_certificate
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class CourseHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = CourseService()
        self.lesson_db = LessonService()
        self.user_db = UserService()
        self.kb = CourseKeyboard()
        self.base_kb = BaseKeyboard()
        self.lesson_kb = LessonKeyboard()
        self.emoji_list = None

    def handle(self):

        @self.router.message(F.text == BUTTONS['EDUCATION'])
        async def get_course(message: Message, state: FSMContext):
            """Отлов кнопки 'Обучение' и вывод списка доступных курсов"""

            await state.update_data(chat_id=message.chat.id)

            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)

            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                msg_text = await self.db.get_msg_by_key('YOUR_PROMOCODE_IS_EXPIRED')
                await message.answer(
                    msg_text,
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

                courses_by_bot = await self.db.get_courses_by_bot(message.chat.id)
                courses_by_promo = await self.db.get_courses_by_promo(message.chat.id)
                all_courses = list(set(courses_by_bot + courses_by_promo))
                all_courses.sort(key=lambda elem: elem.get('order_num'))

                if promocode.type_id == 3:
                    all_courses = await self.db.get_all_courses()
                    all_courses = list(set(all_courses))
                    all_courses.sort(key=lambda elem: elem.get('order_num'))

                user = await self.db.get_user_by_tg_id(message.chat.id)

                # ---------------------Логика для перехода сразу к списку уроков, если курс всего 1-----------------
                if len(all_courses) == 1:
                    course = await self.db.get_course_by_name(all_courses[0].get('title'))
                    logger.debug(f"Пользователь {message.from_user.id} перешел на курс: {course}")
                    await state.update_data(course_id=course.id)
                    course_history = await self.db.get_or_create_history(
                        user=user,
                        course_id=course.id,
                    )

                    if course_history.is_show_description:
                        await show_course_intro_first_time(
                            course=course,
                            message=message,
                            self=self,
                            state=state,
                            course_history=course_history,
                            user_id=user.id,
                            promocode=promocode
                        )

                        # устанавливаем отлов состояния на название урока
                        await state.set_state(LessonChooseState.lesson)

                        msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
                        await message.answer(
                            msg_text,
                            reply_markup=await self.base_kb.menu_btn()
                        )
                    else:
                        lesson = await self.lesson_db.get_last_passed_lesson(
                            tg_id=message.chat.id,
                            course_id=course.id
                        )
                        await state.update_data(lesson=lesson)
                        if isinstance(lesson, Lessons):
                            await state.update_data(lesson_id=lesson.id)

                        if lesson == 'all_lesson_done':

                            msg = await message.answer(
                                course.outro,
                                reply_markup=await self.lesson_kb.lessons_btn(course.id, user.id, promocode)
                            )

                            # устанавливаем отлов состояния на название урока
                            await state.set_state(LessonChooseState.lesson)
                            await state.update_data(msg=msg.message_id)

                            msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
                            menu_msg = await message.answer(
                                msg_text,
                                reply_markup=await self.base_kb.menu_btn(course.certificate_img)
                            )

                            await state.update_data(menu_msg=menu_msg.message_id)

                        else:
                            # создаем запись истории прохождения урока
                            await self.lesson_db.create_history(
                                lesson_id=lesson.id,
                                user_id=user.id,
                                course_history_id=course_history.id
                            )

                            await show_lesson_info(
                                self=self,
                                lesson=lesson,
                                state=state,
                                message=message,
                                user_id=user.id
                            )

                            msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
                            await message.answer(
                                msg_text,
                                reply_markup=await self.base_kb.menu_btn()
                            )

                # -------------------------Логика если курсов больше 1----------------------------------

                else:
                    user = await self.db.get_user_by_tg_id(message.chat.id)
                    courses_ids = [course.get('id') for course in all_courses]
                    courses_with_history = await self.db.get_courses_by_ids(
                        user_id=user.id,
                        courses_ids=courses_ids
                    )
                    all_courses = add_course_without_history(
                        all_courses=all_courses,
                        courses_with_history=courses_with_history
                    )
                    all_courses.sort(key=lambda elem: elem.get('order_num'))
                    msg_text = await self.db.get_msg_by_key('CHOOSE_COURSE')
                    msg = await message.answer(
                        msg_text,
                        reply_markup=await self.kb.courses_btn(all_courses)
                    )
                    logger.debug(f"Пользователь {message.chat.id} получил на курсы: {all_courses}")

                    await state.update_data(msg=msg.message_id)
                    await state.set_state(CourseChooseState.course)

                    msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
                    await message.answer(
                        msg_text,
                        reply_markup=await self.base_kb.menu_btn()
                    )

        @self.router.callback_query(or_f(CourseChooseState.course, F.data.startswith('course')))
        async def get_lesson(callback: CallbackQuery, state: FSMContext):
            """Отлавливаем выбранный пользователем курс"""

            await state.update_data(chat_id=callback.message.chat.id)

            try:
                await callback.bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=None
                )
            except Exception:
                pass

            data = await state.get_data()
            user = await self.db.get_user_by_tg_id(callback.message.chat.id)
            course_id = callback.data.split('_')[-1]
            await state.update_data(course_id=course_id)
            course = await self.db.get_course_by_id(course_id)
            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)

            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                msg_text = await self.db.get_msg_by_key('YOUR_PROMOCODE_IS_EXPIRED')
                await callback.message.answer(
                    msg_text,
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

                await delete_messages(
                    src=callback.message,
                    data=data,
                    state=state
                )

                if course:
                    course_history = await self.db.get_or_create_history(
                        course_id=course.id,
                        user=user
                    )
                    if course_history.is_show_description:
                        await show_course_intro_first_time(
                            course=course,
                            message=callback.message,
                            self=self,
                            state=state,
                            course_history=course_history,
                            user_id=user.id,
                            promocode=promocode
                        )

                        # устанавливаем отлов состояния на название урока
                        await state.set_state(LessonChooseState.lesson)

                    else:
                        msg_text = await self.db.get_msg_by_key('LESSONS_LIST')
                        msg = await callback.message.answer(
                            msg_text.format(
                                course.title
                            ),
                            reply_markup=await self.lesson_kb.lessons_btn(course.id, user.id, promocode)
                        )
                        await state.update_data(msg=msg.message_id)

                    certificate = None
                    if promocode.type_id == 3:
                        certificate = course.certificate_img

                    msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
                    await callback.message.answer(
                        msg_text,
                        reply_markup=await self.base_kb.menu_btn(certificate)
                    )

                    # устанавливаем отлов состояния на название урока
                    await state.set_state(LessonChooseState.lesson)

                else:
                    promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
                    courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                    msg_text = await self.db.get_msg_by_key('MENU')
                    await callback.message.answer(
                        msg_text,
                        reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                    )

        @self.router.message(F.text == BUTTONS['GET_CERTIFICATE'])
        async def get_certificate(message: Message, state: FSMContext):
            """Отлов кнопки 'Получить сертификат' и его выдача"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            course_id = data.get('course_id')
            course = await self.db.get_course_by_id(course_id)
            msg_text = await self.db.get_msg_by_key('CERTIFICATE')
            await message.answer(
                msg_text
            )

            fullname = await self.user_db.get_fullname_by_tg_id(message.chat.id)
            if not fullname:
                fullname = message.from_user.first_name if message.from_user.first_name else ''\
                           + message.from_user.last_name if message.from_user.last_name else ''

            # формируем сертификат
            build_certificate(
                user_id=message.chat.id,
                fullname=fullname,
                course_name=course.title
            )

            # читаем файл и отправляем пользователю
            file_path = f'/app/static/certificate_{message.chat.id}.pdf'
            certificate = FSInputFile(file_path)
            logger.debug(f"Пользователь {message.chat.id}, {file_path} === {certificate}")

            await message.bot.send_document(
                chat_id=data.get('chat_id'),
                document=certificate
            )

            msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
            await message.answer(
                msg_text,
                reply_markup=await self.base_kb.menu_btn()
            )

        @self.router.callback_query(F.data.startswith('continue_'))
        async def get_course_by_notify(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки из уведомления 'продолжить обучение' и вывод списка доступных курсов"""

            await state.update_data(chat_id=callback.message.chat.id)

            try:
                await callback.bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=None
                )
            except Exception:
                pass

            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
            user = await self.db.get_user_by_tg_id(callback.message.chat.id)

            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                msg_text = await self.db.get_msg_by_key('YOUR_PROMOCODE_IS_EXPIRED')
                await callback.message.answer(
                    msg_text,
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

                courses_by_bot = await self.db.get_courses_by_bot(callback.message.chat.id)
                courses_by_promo = await self.db.get_courses_by_promo(callback.message.chat.id)
                all_courses = list(set(courses_by_bot + courses_by_promo))
                all_courses.sort(key=lambda elem: elem.get('order_num'))

                if promocode.type_id == 3:
                    all_courses = await self.db.get_all_courses()
                    all_courses = list(set(all_courses))
                    all_courses.sort(key=lambda elem: elem.get('order_num'))

                if len(all_courses) > 1:
                    all_courses_not_completed = await self.db.get_not_completed_course(
                        user_id=user.id,
                        promocode=promocode.code
                    )
                    if all_courses_not_completed:
                        all_courses = [random.choice(all_courses_not_completed)]

                # ---------------------Логика для перехода сразу к списку уроков, если курс всего 1-----------------
                course = await self.db.get_course_by_name(all_courses[0].get('title'))
                logger.debug(f"Пользователь {callback.message.chat.id} перешел на курс: {course}")
                await state.update_data(course_id=course.id)
                course_history = await self.db.get_or_create_history(
                    user=user,
                    course_id=course.id,
                )

                if course_history.is_show_description:
                    await show_course_intro_first_time(
                        course=course,
                        message=callback.message,
                        self=self,
                        state=state,
                        course_history=course_history,
                        user_id=user.id,
                        promocode=promocode
                    )

                    # устанавливаем отлов состояния на название урока
                    await state.set_state(LessonChooseState.lesson)

                    msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
                    await callback.message.answer(
                        msg_text,
                        reply_markup=await self.base_kb.menu_btn()
                    )
                else:
                    lesson = await self.lesson_db.get_last_passed_lesson(
                        tg_id=callback.message.chat.id,
                        course_id=course.id
                    )
                    await state.update_data(lesson=lesson)
                    if isinstance(lesson, Lessons):
                        await state.update_data(lesson_id=lesson.id)

                    if lesson == 'all_lesson_done':

                        msg = await callback.message.answer(
                            course.outro,
                            reply_markup=await self.lesson_kb.lessons_btn(course.id, user.id, promocode)
                        )

                        # устанавливаем отлов состояния на название урока
                        await state.set_state(LessonChooseState.lesson)
                        await state.update_data(msg=msg.message_id)

                        msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
                        menu_msg = await callback.message.answer(
                            msg_text,
                            reply_markup=await self.base_kb.menu_btn(course.certificate_img)
                        )

                        await state.update_data(menu_msg=menu_msg.message_id)

                    else:
                        # создаем запись истории прохождения урока
                        await self.lesson_db.create_history(
                            lesson_id=lesson.id,
                            user_id=user.id,
                            course_history_id=course_history.id
                        )

                        await show_lesson_info(
                            self=self,
                            lesson=lesson,
                            state=state,
                            message=callback.message,
                            user_id=user.id
                        )

                        msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
                        await callback.message.answer(
                            msg_text,
                            reply_markup=await self.base_kb.menu_btn()
                        )
