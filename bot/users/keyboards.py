from aiogram.types import (InlineKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.courses.service import CourseService
from bot.quiz.service import QuizService
from bot.users.service import UserService
from bot.utils.buttons import BUTTONS
from bot.utils.constants import EMPTY


class UserKeyboard:
    def __init__(self):
        self.db = UserService()

    async def manager_btn(self) -> ReplyKeyboardMarkup:
        """Кнопка на главное меню"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['GENERATE_PROMOCODE']),
        )
        builder.row(
            KeyboardButton(text=BUTTONS['SEE_PROMOCODES']),
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU']),
        )
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def choose_role_btn(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        roles = await UserService.get_promocode_roles()

        for role in roles:
            builder.button(
                text=role,
                callback_data=f'role_{role}'
            )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def choose_course_btn(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        courses = await CourseService.get_all_courses()

        for course in courses:
            builder.button(
                text=course,
                callback_data=f'course_{course}'
            )

        builder.button(
            text='Не выбирать',
            callback_data=f'course_{EMPTY}'
        )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def choose_quiz_btn(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        quizes = await QuizService.get_all_quizes()

        for quiz in quizes:
            builder.button(
                text=quiz,
                callback_data=f'quiz_{quiz[:30]}'
            )

        builder.button(
            text='Не выбирать',
            callback_data=f'quiz_{EMPTY}'
        )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
