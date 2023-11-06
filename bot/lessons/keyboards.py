from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.lessons.models import Lessons
from bot.lessons.service import LessonService
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class LessonKeyboard:
    def __init__(self):
        self.db = LessonService()

    async def lesson_menu_btn(self, lesson: Lessons):
        builder = InlineKeyboardBuilder()
        builder.button(
            text=BUTTONS['BACK'],
            callback_data=f'back_{lesson.course_id}'
        )
        if lesson.questions:

            builder.button(
                text=BUTTONS['START_TEST'],
                callback_data=f'start_test_{lesson.course_id}'
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

    async def test_answers_btn(self, count_answers: int, selected: list[int] = None):
        builder = InlineKeyboardBuilder()
        for num in range(1, count_answers + 1):
            if selected and num in selected:
                builder.button(
                    text=f'{num} ✅',
                    callback_data=f'test_answers_{num}'
                )
                continue
            builder.button(
                text=str(num),
                callback_data=f'test_answers_{num}'
            )
        builder.button(
            text='Проверить ответ',
            callback_data='check_answer'
        )
        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def next_question_btn(self):
        builder = InlineKeyboardBuilder()
        builder.button(
            text='Следующий вопрос',
            callback_data='next_question'
        )
        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def next_lesson_btn(self, lesson: Lessons = None):
        builder = ReplyKeyboardBuilder()
        builder.button(
            text=lesson.title
        )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder=MESSAGES['NEXT_LESSON'],
        )

