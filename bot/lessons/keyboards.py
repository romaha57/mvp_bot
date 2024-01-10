from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.lessons.models import Lessons
from bot.lessons.service import LessonService
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class LessonKeyboard:
    def __init__(self):
        self.db = LessonService()

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

    async def lessons_btn(self, course_id: str, user_id: int) -> InlineKeyboardMarkup:
        """Кнопки со списком уроков"""

        builder = InlineKeyboardBuilder()
        lessons_from_db = await self.db.get_lessons(course_id, user_id)

        if not lessons_from_db:
            # получаем первый урок, чтобы не отображать весь список уроков
            first_lesson = await self.db.get_first_lesson(course_id)
            builder.button(
                text=first_lesson,
                callback_data=f'lesson_{first_lesson[:20]}'
            )

            builder.adjust(1)

            return builder.as_markup(
                resize_keyboard=True,
                input_field_placeholder=MESSAGES['CHOOSE_LESSONS'],
                one_time_keyboard=True
            )

        for lesson in lessons_from_db:
            if lesson['status_id'] == 4:
                builder.button(
                    text=lesson['title'] + '✅',
                    callback_data=f'lesson_{lesson["title"][:20]}'
                )
            elif lesson['status_id'] == 3:
                builder.button(
                    text=lesson['title'] + '❗',
                    callback_data=f'lesson_{lesson["title"][:20]}'
                )
            elif lesson['status_id'] in (1, 2):
                builder.button(
                    text=lesson['title'] + '👀 ',
                    callback_data=f'lesson_{lesson["title"][:20]}'
                )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=MESSAGES['CHOOSE_LESSONS'],
            one_time_keyboard=True
        )

    async def test_answers_btn(self, count_answers: int, selected: list[int] = None) -> InlineKeyboardMarkup:
        """Кнопки с вариантами ответа на тестовые вопросы после урока"""

        letter_list = ['1', 'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И']

        builder = InlineKeyboardBuilder()
        for num in range(1, count_answers + 1):
            if selected and num in selected:
                builder.button(
                    text=f'Вариант {letter_list[num]} ✅',
                    callback_data=f'test_answers_{num}'
                )
                continue
            builder.button(
                text=f'Вариант {letter_list[num]}',
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

    async def next_question_btn(self, test_questions: list[dict]) -> InlineKeyboardMarkup:
        """Кнопка с переходом к следующему вопросу в тесте после урока"""

        builder = InlineKeyboardBuilder()
        if len(test_questions) == 0:
            builder.button(
                text='Завершить тест',
                callback_data='next_question'
            )
        else:
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
            callback_data=f'lesson_{lesson.title[:20]}'

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

    async def start_again_lesson(self, lesson: Lessons) -> InlineKeyboardMarkup:
        """Кнопка для повторного прохождения урока"""

        builder = InlineKeyboardBuilder()
        builder.button(
            text=BUTTONS['AGAIN'],
            callback_data=f'lesson_{lesson.title[:20]}'
        )
        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def additional_task_btn(self):
        """Кнопки меню при выдаче доп задания к уроку (Пропустить, Выполнил)"""

        builder = InlineKeyboardBuilder()
        builder.button(
            text=BUTTONS['SKIP'],
            callback_data='skip_additional_task'
        )
        builder.button(
            text=BUTTONS['DONE'],
            callback_data='done_additional_task'
        )
        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
