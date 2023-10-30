from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.quiz.service import QuizService
from bot.utils.messages import MESSAGES


class QuizKeyboard:
    def __init__(self):
        self.db = QuizService()


    async def quiz_answers(self, question_id: int):
        builder = InlineKeyboardBuilder()
        answers = await self.db.get_quiz_answers(question_id)
        for answer in answers:
            builder.button(
                    text=answer.title,
                    callback_data=f'answer_{answer.id}'
            )
        builder.adjust(1)
        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder=MESSAGES['QUIZ_ANSWERS'],
            one_time_keyboard=True
        )
