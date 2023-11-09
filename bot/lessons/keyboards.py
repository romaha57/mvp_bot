from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.lessons.models import Lessons
from bot.lessons.service import LessonService
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class LessonKeyboard:
    def __init__(self):
        self.db = LessonService()

    async def lesson_menu_btn(self, lesson: Lessons) -> InlineKeyboardMarkup:
        """Кнопки меню для урока"""

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

    async def lessons_btn(self, course_id: str, user_id: int) -> InlineKeyboardMarkup:
        """Кнопки со списком уроков"""

        builder = InlineKeyboardBuilder()
        lessons_from_db = await self.db.get_lessons(course_id)

        result = {}
        # сортируем список уроков по порядковому номеру и статусу
        sorted_lessons_by_status_id = sorted(lessons_from_db, key=lambda elem: (elem['order_num'], elem['status_id']))
        for lesson in sorted_lessons_by_status_id:
            result[lesson['title']] = (lesson['status_id'], lesson['user_id'])

        # формируем кнопки в зависимости от статуса прохождения урока
        # при успешном прохождении - '✅'(id статуса = 4)
        # при заваленном тесте - '❗' (id статуса = 3)
        for lesson in result:
            if result[lesson][0] == 4 and result[lesson][1] == user_id:
                builder.button(
                    text=lesson + '✅',
                    callback_data=lesson
                )
            elif result[lesson][0] == 3 and result[lesson][1] == user_id:
                builder.button(
                    text=lesson + '❗',
                    callback_data=lesson
                )
            else:
                builder.button(
                        text=lesson,
                        callback_data=lesson
                )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=MESSAGES['CHOOSE_LESSONS'],
            one_time_keyboard=True
        )

    async def test_answers_btn(self, count_answers: int, selected: list[int] = None) -> InlineKeyboardMarkup:
        """Кнопки с вариантами ответа на тестовые вопросы после урока"""

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

        builder.adjust(2)

        # кнопка 'проверить ответ' добавляет нижним рядом
        builder.row(InlineKeyboardButton(
            text='Проверить ответ',
            callback_data='check_answer'
        ))

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def next_question_btn(self) -> InlineKeyboardMarkup:
        """Кнопка с переходом к следующему вопросу в тесте после урока"""

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

    async def next_lesson_btn(self, lesson: Lessons = None) -> InlineKeyboardMarkup:
        """Кнопка для перехода к следующему уроку"""

        builder = InlineKeyboardBuilder()
        builder.button(
            text=lesson.title,
            callback_data=lesson.title

        )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder=MESSAGES['NEXT_LESSON'],
        )

    async def close_lesson_btn(self, lesson: Lessons) -> InlineKeyboardMarkup:
        """Кнопки меню для урока"""

        builder = InlineKeyboardBuilder()
        builder.button(
            text=BUTTONS['CLOSE_LESSON'],
            callback_data=f'close_lesson_{lesson.course_id}'
        )
        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
