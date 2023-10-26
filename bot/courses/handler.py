from aiogram import Bot, Router

from bot.courses.service import CourseService
from bot.handlers.base_handler import Handler


class CourseHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = CourseService()

    def handle(self):
        pass
