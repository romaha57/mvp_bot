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
            msg = message.text.split()

            # если у пользователя есть в ссылку промокод, то получаем его
            if len(msg) >= 2:
                promocode = msg[-1]
            else:
                promocode = '-'
            await message.answer('Я такой-то бот, делаю то-то и то-то\n'
                                 f'Ваш промокод: {promocode}')

        @self.router.message(Command('id'))
        async def get_tg_id(message: Message):
            user_id = str(message.from_user.id)
            await message.answer(f'Ваш id - {user_id}')
