from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.settings.service import SettingsService
from bot.users.models import Promocodes

from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class BaseKeyboard:
    def __init__(self):
        self.db = SettingsService()

    async def _get_button(self, name):
        """Получение текста кнопки"""
        return BUTTONS.get(name)

    async def start_btn(self, promocode: Promocodes):
        """Стартовое меню бота"""

        builder = ReplyKeyboardBuilder()

        if promocode.quiz_id and promocode.course_id:
            builder.row(
                KeyboardButton(text=await self._get_button('QUIZ')),
                KeyboardButton(text=await self._get_button('EDUCATION')),
                KeyboardButton(text=await self._get_button('RESULTS_QUIZ')),
            )

        elif promocode.quiz_id:
            builder.row(
                KeyboardButton(text=await self._get_button('QUIZ')),
            )
        elif promocode.course_id:
            builder.row(
                KeyboardButton(text=await self._get_button('EDUCATION')),
            )

        builder.row(
            KeyboardButton(text=await self._get_button('REFERAL')),
            KeyboardButton(text=await self._get_button('MENU'))
        )

        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=MESSAGES['KB_PLACEHOLDER'],
            one_time_keyboard=True
        )

    async def help_btn(self):
        """Кнопка для обращения в службу поддержки"""

        builder = ReplyKeyboardBuilder()
        builder.button(
           text=BUTTONS['HELP']
        )
        builder.button(
            text=BUTTONS['MENU']
        )
        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=MESSAGES['KB_PLACEHOLDER'],
            one_time_keyboard=True
        )

    async def menu_btn(self):
        """Кнопка на главное меню"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=await self._get_button('MENU')),
        )
        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=MESSAGES['KB_PLACEHOLDER'],
            one_time_keyboard=True
        )