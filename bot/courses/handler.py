import traceback

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from loguru import logger

from bot.courses.keyboards import CourseKeyboard
from bot.courses.service import CourseService
from bot.courses.states import CourseChooseState
from bot.handlers.base_handler import Handler
from bot.lessons.keyboards import LessonKeyboard
from bot.lessons.service import LessonService
from bot.lessons.states import LessonChooseState
from bot.settings.keyboards import BaseKeyboard
from bot.users.service import UserService
from bot.utils.answers import show_lesson_info
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

            data = await state.get_data()
            await state.update_data(chat_id=message.chat.id)

            # получаем id бота текущего юзера и id курса для текущего пользователя и его промокода
            user_data = await self.db.get_bot_id_and_promocode_course_id_by_user(
                tg_id=message.from_user.id
            )

            user = await self.db.get_user_by_tg_id(message.chat.id)

            all_courses = await self.db.get_course_by_promo_and_bot(
                bot_id=user_data['bot_id'],
                promocode_course_id=user_data['course_id']
            )

            # ---------------------Логика для перехода сразу к списку уроков, если курс всего 1-----------------
            if len(all_courses) == 1:
                course = await self.db.get_course_by_name(all_courses[0])
                logger.debug(f"Пользователь {message.from_user.id} перешел на курс: {course}")

                await state.update_data(course_id=course.id)
                # создаем запись в истории прохождения курса со статусом 'Открыт'
                await self.db.create_history(
                    course_id=course.id,
                    tg_id=message.chat.id
                )

                if user.is_show_course_description:
                    # убираем флаг у юзера, чтобы ему больше не показывалось видео курса
                    await self.db.mark_user_show_course_description(user, False)

                    # выводим приветственное видео курса, если оно есть
                    if course.intro_video:
                        await message.answer_video(
                            video=course.intro_video
                        )

                    await message.answer(course.title)

                    msg = await message.answer(
                        course.intro,
                        reply_markup=await self.lesson_kb.lessons_btn(course.id, user.id)
                    )

                    # устанавливаем отлов состояния на название урока
                    await state.set_state(LessonChooseState.lesson)

                    await state.update_data(chat_id=message.chat.id)
                    await state.update_data(delete_message_id=msg.message_id)

                    menu_msg = await message.answer(
                        MESSAGES['GO_TO_MENU'],
                        reply_markup=await self.base_kb.menu_btn()
                    )

                    await state.update_data(menu_msg=menu_msg.message_id)

                else:

                    # сразу переводим пользователя на последний урок, после нажатия на 'Обучение'

                    # получаем актуальную для текущего пользователя попытку прохождения курса
                    actual_course_attempt = await self.db.get_actual_course_attempt(
                        user_id=user.id,
                        course_id=course.id
                    )

                    lesson = await self.lesson_db.get_last_passed_lesson(
                        tg_id=message.from_user.id,
                        course_id=course.id
                    )

                    # когда все уроки пройдены и нет следующего урока, то выводим сообщение об этом
                    if lesson == 'all_lesson_done':

                        msg = await message.answer(
                            course.intro,
                            reply_markup=await self.lesson_kb.lessons_btn(course.id, user.id)
                        )

                        # устанавливаем отлов состояния на название урока
                        await state.set_state(LessonChooseState.lesson)
                        await state.update_data(delete_message_id=msg.message_id)

                        if course.certificate_img:
                            menu_msg = await message.answer(
                                MESSAGES['GO_TO_MENU'],
                                reply_markup=await self.base_kb.menu_btn_with_certificate()
                            )

                            await state.update_data(menu_msg=menu_msg.message_id)

                        else:
                            menu_msg = await message.answer(
                                MESSAGES['GO_TO_MENU'],
                                reply_markup=await self.base_kb.menu_btn()
                            )

                            await state.update_data(menu_msg=menu_msg.message_id)

                    else:
                        # создаем запись истории прохождения урока
                        await self.lesson_db.create_history(
                            lesson_id=lesson.id,
                            user_id=user.id,
                            course_history_id=actual_course_attempt.id
                        )

                        await state.update_data(lesson_id=lesson.id)

                        await show_lesson_info(
                            self=self,
                            lesson=lesson,
                            state=state,
                            message=message,
                            user_id=user.id
                        )

                        menu_msg = await message.answer(
                            MESSAGES['GO_TO_MENU'],
                            reply_markup=await self.base_kb.menu_btn()
                        )

                        await state.update_data(menu_msg=menu_msg.message_id)

            # -------------------------Логика если курсов больше 1----------------------------------

            else:
                # устанавливаем отлов состояния на название урока
                await state.set_state(LessonChooseState.lesson)

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
        async def get_lesson(callback: CallbackQuery, state: FSMContext, course: str = None):
            """Отлавливаем выбранный пользователем курс"""

            data = await state.get_data()
            user = await self.db.get_user_by_tg_id(callback.message.chat.id)
            if not course:
                course = await self.db.get_course_by_name(callback.data)
            else:
                course = course

            await state.update_data(course_id=course.id)

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

                if user.is_show_course_description:
                    # выводим приветственное видео курса, если оно есть
                    if course.intro_video:
                        await callback.message.answer_video(
                            video=course.intro_video
                        )

                    await callback.message.answer(course.title)

                    msg = await callback.message.answer(
                        course.intro,
                        reply_markup=await self.lesson_kb.lessons_btn(course.id, user.id)
                    )
                    await state.update_data(chat_id=callback.message.chat.id)
                    await state.update_data(delete_message_id=msg.message_id)
                else:
                    msg = await callback.message.answer(
                        'Уроки курса:',
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
                promocode = await self.db.get_promocode(data.get('promocode_id'))
                await callback.message.answer(
                    MESSAGES['MENU'],
                    reply_markup=await self.base_kb.start_btn(promocode=promocode)
                )

        @self.router.message(F.text == BUTTONS['GET_CERTIFICATE'])
        async def get_certificate(message: Message, state: FSMContext):
            """Отлов кнопки 'Получить сертификат' и его выдача"""

            data = await state.get_data()
            course_id = data.get('course_id')
            course = await self.db.get_course_by_id(course_id)

            await message.answer(
                MESSAGES['CERTIFICATE']
            )

            fullname = await self.user_db.get_fullname_by_tg_id(message.from_user.id)

            # формируем сертификат
            build_certificate(
                user_id=message.chat.id,
                fullname=fullname,
                course_name=course.title
            )

            # читаем файл и отправляем пользователю
            file_path = f'/app/static/certificate_{message.chat.id}.pdf'
            certificate = FSInputFile(file_path)
            logger.debug(f"Пользователь {message.from_user.id}, {file_path} === {certificate}")
            await message.bot.send_document(
                chat_id=data.get('chat_id'),
                document=certificate
            )

            menu_msg = await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=await self.base_kb.menu_btn()
            )

            await state.update_data(menu_msg=menu_msg.message_id)
            await state.set_state(state=None)
