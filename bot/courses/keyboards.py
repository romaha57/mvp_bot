from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.courses.service import CourseService
from bot.lessons.models import Lessons
from bot.lessons.service import LessonService
from bot.services.base_service import BaseService
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class CourseKeyboard:
    def __init__(self):
        self.db = CourseService()
        self.lesson_db = LessonService()

    async def courses_btn(self, courses: list[dict]) -> InlineKeyboardMarkup:
        """Кнопки со списком доступных курсов"""

        builder = InlineKeyboardBuilder()
        for course in courses:
            course_status = course.get('status_id')
            if course_status == 2:
                builder.button(
                    text=f"{course.get('title')} ✅",
                    callback_data=f"course_{course.get('id')}"
                )

            elif course_status == 1:
                builder.button(
                    text=f"{course.get('title')} 👀",
                    callback_data=f"course_{course.get('id')}"
                )

            else:
                builder.button(
                    text=course.get('title'),
                    callback_data=f"course_{course.get('id')}"
                )

        builder.adjust(1)
        msg_text = await BaseService.get_msg_by_key('CHOOSE_COURSE')
        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=msg_text,
            one_time_keyboard=True
        )

    async def lesson_menu_btn(self, lesson: Lessons, emoji_list: list = None) -> InlineKeyboardMarkup:
        """Кнопки меню для урока"""

        builder = InlineKeyboardBuilder()

        # отрисовываем кнопки со смайликами
        if emoji_list:
            for emoji in emoji_list:
                builder.add(
                    InlineKeyboardButton(
                        text=f'{emoji["button"]}({emoji["count"]})',
                        callback_data=f'emoji_{emoji["button"]}'
                    )
                )

        builder.button(
            text=BUTTONS['BACK'],
            callback_data=f'back_{lesson.course_id}'
        )
        if lesson.work_type_id != 1:

            builder.button(
                text=BUTTONS['START_TASK'],
                callback_data=f'start_task_{lesson.course_id}'
            )
        else:
            builder.button(
                text=BUTTONS['CLOSE_LESSON'],
                callback_data=f'close_lesson_{lesson.course_id}'
            )
        builder.adjust(3)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
