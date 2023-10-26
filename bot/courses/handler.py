from aiogram import Bot, Router

from bot.courses.keyboards import CourseKeyboard
from bot.courses.service import CourseService
from bot.handlers.base_handler import Handler


class CourseHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = CourseService()
        self.keyboard = CourseKeyboard()

    def handle(self):
        pass
