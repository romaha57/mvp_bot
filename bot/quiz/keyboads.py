from aiogram.types import (InlineKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.quiz.service import QuizService
from bot.services.base_service import BaseService
from bot.users.models import Promocodes
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class QuizKeyboard:
    def __init__(self):
        self.db = QuizService()

    async def quizes_list_btn(self, quizes: list[dict]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for quiz in quizes:
            builder.button(
                text=quiz.get('name'),
                callback_data=f'quiz_{quiz.get("id")}'
            )
        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def quiz_answers(self, question_id: int) -> InlineKeyboardMarkup:
        """Кнопки с вариантами ответа на тестирование(quiz)"""

        builder = InlineKeyboardBuilder()

        answers = await self.db.get_quiz_answers(question_id)
        for answer in answers:
            builder.button(
                text=answer.title,
                callback_data=f'answer_{answer.id}'
            )
        builder.adjust(1)
        msg_text = await BaseService.get_msg_by_key('QUIZ_ANSWERS')
        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=msg_text,
            one_time_keyboard=True
        )

    async def switch_arrows_result_quiz_btn(self, attempts_list, index):
        """Кнопки для вывода результата тестирования(стрелки)"""

        builder = ReplyKeyboardBuilder()

        # пытаемся получить предыдущую запись
        try:
            attempts_list[index + 1]
        except IndexError:
            pass
        else:
            builder.button(
                text=BUTTONS['PREVIOUS']
            )

        # чтобы не брать элементы по кругу(чтобы индекс не был -1, -2 и так далее)
        if index != 0:
            # пытаемся получить следующую запись
            try:
                attempts_list[index - 1]
            except IndexError:
                pass
            else:
                builder.button(
                    text=BUTTONS['NEXT'],
                )

        builder.button(
            text=BUTTONS['MENU']
        )

        builder.adjust(1)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    async def quiz_menu_btn(self, promocode: Promocodes) -> ReplyKeyboardMarkup:
        """Кнопки управления тестированием """

        builder = ReplyKeyboardBuilder()

        if promocode.is_test:
            quiz_btn = KeyboardButton(text=BUTTONS['TEST_QUIZ'])
        else:
            quiz_btn = KeyboardButton(text=BUTTONS['START_QUIZ'])

        builder.row(
            quiz_btn,
            KeyboardButton(text=BUTTONS['RESULTS_QUIZ'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
