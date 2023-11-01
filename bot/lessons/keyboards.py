from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.lessons.service import LessonService
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class LessonKeyboard:
    def __init__(self):
        self.db = LessonService()

    async def lesson_menu_btn(self, course_id: int):
        builder = InlineKeyboardBuilder()
        builder.button(
            text=BUTTONS['BACK'],
            callback_data=f'back_{course_id}'
        )

        builder.button(
            text=BUTTONS['START_TEST'],
            callback_data=f'start_test_{course_id}'
        )

        builder.button(
            text=BUTTONS['CLOSE_LESSON'],
            callback_data=f'close_lesson_{course_id}'
        )
        builder.adjust(3)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def lessons_btn(self, course_id: str):
        builder = ReplyKeyboardBuilder()
        lessons = await self.db.get_lessons(course_id)
        for lesson in lessons:
            builder.button(
                    text=lesson
            )

        builder.button(
            text=BUTTONS['MENU']
        )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=MESSAGES['CHOOSE_LESSONS'],
            one_time_keyboard=True
        )

    async def test_answers_btn(self, answers: list[dict]):
        builder = InlineKeyboardBuilder()

        for answer in answers:
            builder.button(
                text=answer['title'],
                callback_data=f'test_answer/{answer["title"][:20]}/{answer["good"]}'
            )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

