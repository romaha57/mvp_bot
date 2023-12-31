import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers.main_handler import MainHandler
from bot.middleware import CheckPromocodeMiddleware
from bot.settings_bot import settings

# для удобного импорта модулей
sys.path.append("/Users/macbook/PycharmProjects/mvp_bot")
sys.path.append("bot/")


class MainBot:

    def __init__(self):
        self.bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher(storage=MemoryStorage())
        # self.dp.message.middleware(CheckPromocodeMiddleware())
        self.handler = MainHandler(self.bot)

    async def start(self):
        """Подключение всех роутеров/старт отлова сообщений/логгирование"""

        self.dp.include_router(self.handler.command_handler.router)
        self.dp.include_router(self.handler.course_handler.router)
        self.dp.include_router(self.handler.lesson_handler.router)
        self.dp.include_router(self.handler.quiz_handler.router)
        self.dp.include_router(self.handler.user_handler.router)
        self.dp.include_router(self.handler.text_handler.router)
        self.handler.handle()
        # logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    async def main(self):
        """Основная точка входа в бота и его запуск"""

        await self.start()
        try:
            await self.dp.start_polling(self.bot, polling_timeout=100000)
        except TelegramNetworkError:
            pass


if __name__ == '__main__':
    bot = MainBot()
    print('START BOT')
    asyncio.run(bot.main())
