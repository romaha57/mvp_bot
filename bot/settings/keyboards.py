from typing import Any, Union

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

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

    async def start_btn(self, data: Union[dict, Promocodes]) -> ReplyKeyboardMarkup:
        """Стартовое меню бота"""

        builder = ReplyKeyboardBuilder()

        if isinstance(data, Promocodes):
            builder.row(
                # KeyboardButton(text=await self._get_button('OWNER_QUIZ')),
                KeyboardButton(text=await self._get_button('OWNER_EDUCATION')),
            )
        else:

            if data.get('courses') and data.get('quizes'):
                builder.row(
                    # KeyboardButton(text=await self._get_button('QUIZ')),
                    KeyboardButton(text=await self._get_button('EDUCATION')),
                )

            # if data.get('quizes') and not data.get('courses'):
            #     builder.row(
            #         KeyboardButton(text=await self._get_button('QUIZ')),
            #     )

            elif data.get('courses') and not data.get('quizes'):
                builder.row(
                    KeyboardButton(text=await self._get_button('EDUCATION')),
                )

        builder.row(
            KeyboardButton(text=await self._get_button('KNOWLEDGE_BASE'))
        )

        builder.add(
            KeyboardButton(text=await self._get_button('REFERAL')),
        )
        builder.add(
            KeyboardButton(text=await self._get_button('BALANCE')),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def help_btn(self) -> ReplyKeyboardMarkup:
        """Кнопка для обращения в службу поддержки"""

        builder = ReplyKeyboardBuilder()
        builder.button(
           text=BUTTONS['HELP']
        )
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def menu_btn(self, certificate: Union[Any, None] = False) -> ReplyKeyboardMarkup:
        """Кнопка на главное меню"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=await self._get_button('MENU')),
        )

        if certificate:
            builder.row(
                KeyboardButton(text=await self._get_button('GET_CERTIFICATE')),
            )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def anketa_answer_btn(self, question_id: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text='Ответить',
            callback_data=f'anketa_{question_id}'
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def test_promo_menu(self) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()

        builder.add(
            # KeyboardButton(text=BUTTONS['QUIZ']),
            KeyboardButton(text=BUTTONS['TEST_EDUCATION'])

        )
        builder.row(
            KeyboardButton(text=BUTTONS['KNOWLEDGE_BASE'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def politics_btn(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text='Продолжить ✅',
            callback_data=f'accept_politics'
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
