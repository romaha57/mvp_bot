from aiogram import Bot, Router

from bot.handlers.base_handler import Handler
from bot.users.service import UserService


class UserHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = UserService()

    def handle(self):
        pass