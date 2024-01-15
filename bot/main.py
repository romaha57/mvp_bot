import asyncio
import sys
import traceback

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger

from bot.handlers.main_handler import MainHandler
from bot.settings_bot import settings
from bot.utils.logger import debug_log_write, warning_log_write

# для удобного импорта модулей
sys.path.append("/Users/macbook/PycharmProjects/mvp_bot")
sys.path.append("bot/")


class MainBot:

    def __init__(self):
        self.bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
        storage = RedisStorage.from_url('redis://redis:6379/0')
        self.dp = Dispatcher(storage=storage)
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

    async def start_logging(self):
        """Запуск логгирования"""

        debug_log_write()
        warning_log_write()

    async def main(self):
        """Основная точка входа в бота и его запуск"""

        await self.start_logging()
        await self.start()
        try:
            await self.dp.start_polling(self.bot, polling_timeout=100000)
        except Exception as e:
            logger.warning(str(e), traceback.format_exc())


if __name__ == '__main__':
    bot = MainBot()
    print('START BOT')
    asyncio.run(bot.main())
