from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.courses.models import Course
from bot.courses.service import CourseService
from bot.lessons.service import LessonService
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES





class CourseKeyboard:
    def __init__(self):
        self.db = CourseService()
        self.lesson_db = LessonService()



    async def courses_btn(self, courses: set[Course]):
        builder = ReplyKeyboardBuilder()
        for course in courses:
            builder.button(
                text=course.title
            )

        builder.button(
           text=BUTTONS['MENU']
        )
        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=MESSAGES['CHOOSE_COURSE'],
            one_time_keyboard=True
        )
