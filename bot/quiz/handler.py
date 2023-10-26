from aiogram import Bot, Router

from bot.handlers.base_handler import Handler
from bot.quiz.keyboads import QuizKeyboard
from bot.quiz.service import QuizService


class QuizHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = QuizService()
        self.keyboard = QuizKeyboard()

    def handle(self):
        pass