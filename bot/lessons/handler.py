from aiogram import Bot, Router

from bot.handlers.base_handler import Handler
from bot.lessons.keyboards import LessonKeyboard
from bot.lessons.service import LessonService


class LessonHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = LessonService()
        self.keyboard = LessonKeyboard()

    def handle(self):
        pass
