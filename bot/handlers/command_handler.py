from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.settings.service import SettingsService


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = SettingsService()

    def handle(self):
        @self.router.message(Command('start'))
        async def start(message: Message):
            start_msg = await self.db.get_msg_by_key('intro')
            await message.answer(start_msg)

        @self.router.message(Command('id'))
        async def get_tg_id(message: Message):
            user_id = str(message.from_user.id)
            await message.answer(f'Ваш id - {user_id}')
