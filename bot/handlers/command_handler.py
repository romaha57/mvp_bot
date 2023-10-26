from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.handlers.base_handler import Handler


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()

    def handle(self):
        @self.router.message(Command('start'))
        async def start(message: Message):
            await message.answer('Hello')
