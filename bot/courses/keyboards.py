from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.courses.models import Course
from bot.courses.service import CourseService
from bot.lessons.service import LessonService
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class CourseKeyboard:
    def __init__(self):
        self.db = CourseService()
        self.lesson_db = LessonService()

    async def courses_btn(self, courses: list[str]) -> InlineKeyboardMarkup:
        """Кнопки со списком доступных курсов"""

        builder = InlineKeyboardBuilder()
        for course in courses:
            builder.button(
                text=course,
                callback_data=course
            )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=MESSAGES['CHOOSE_COURSE'],
            one_time_keyboard=True
        )
