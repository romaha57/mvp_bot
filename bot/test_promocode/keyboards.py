from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.utils.buttons import BUTTONS


class TestPromoKeyboard:

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
