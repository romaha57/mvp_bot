import asyncio
import pprint
import sys
import traceback

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent
from loguru import logger

from bot.db_connect import Base, engine
from bot.handlers.main_handler import MainHandler
from bot.settings.keyboards import BaseKeyboard
from bot.settings_bot import settings
from bot.test_promocode.utils import is_valid_test_promo
from bot.users.service import UserService
from bot.users.states import UserReport
from bot.utils.delete_messages import delete_messages
from bot.utils.logger import debug_log_write, warning_log_write
from bot.utils.messages import MESSAGES

# для удобного импорта модулей
sys.path.append("/Users/macbook/PycharmProjects/mvp_bot")
sys.path.append("bot/")


class MainBot:

    def __init__(self):
        self.bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
        if settings.debug:
            storage = MemoryStorage()
        else:
            storage = RedisStorage.from_url('redis://redis:6379/0')
        self.dp = Dispatcher(storage=storage)
        # self.dp.message.middleware(CheckPromocodeMiddleware())
        self.handler = MainHandler(self.bot)
        self.kb = BaseKeyboard()
        self.db = UserService()

    async def catch_errors(self):
        """Отлов всех ошибок в хендлерах и логгирование"""

        @self.dp.errors()
        async def catch_error(event: ErrorEvent, state: FSMContext):
            try:
                data = await state.get_data()
                error_data: dict = event.model_dump()
                if error_data.get('update', {}).get('message'):
                    chat_id = error_data.get('update', {}).get('message', {}).get('from_user', {}).get('id')
                else:
                    chat_id_callback = error_data.get('update', {}).get('callback_query', {}).get('from_user', {}).get('id')
                    chat_id = chat_id_callback
                error = error_data.get('exception')
                error_text = f'User: {chat_id}, err: {error}'

                await delete_messages(
                    src=event.update.bot,
                    data=data,
                    state=state
                )

                logger.warning(error_text)
                logger.warning(traceback.format_exc())
                logger.debug(f'Пользователь: {chat_id} получил ошибку: {error_text}')

                promocode = await self.db.get_promocode_by_tg_id(chat_id)
                if promocode.is_test:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=MESSAGES['TEST_PROMO_MENU'],
                        reply_markup=await self.kb.test_promo_menu()
                    )

                else:
                    courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                    if promocode.type_id == 3:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=MESSAGES['ERROR_IN_HANDLER'].format(
                                chat_id
                            ),
                            reply_markup=await self.kb.start_btn(promocode))

                    elif promocode and courses_and_quizes:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=MESSAGES['ERROR_IN_HANDLER'].format(
                                chat_id
                            ),
                            reply_markup=await self.kb.start_btn(courses_and_quizes)
                        )

                    else:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=MESSAGES['ERROR_IN_HANDLER'].format(
                                chat_id
                            ),
                            reply_markup=await self.kb.menu_btn()
                        )
            except Exception as e:
                logger.warning(e)
                logger.warning(traceback.format_exc())

    async def start(self):
        """Подключение всех роутеров/старт отлова сообщений/логгирование"""

        self.dp.include_router(self.handler.command_handler.router)
        self.dp.include_router(self.handler.course_handler.router)
        self.dp.include_router(self.handler.lesson_handler.router)
        self.dp.include_router(self.handler.quiz_handler.router)
        self.dp.include_router(self.handler.user_handler.router)
        self.dp.include_router(self.handler.knowledge_handler.router)
        self.dp.include_router(self.handler.test_promo_handler.router)
        self.dp.include_router(self.handler.text_handler.router)
        self.handler.handle()
        # logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    async def start_logging(self):
        """Запуск логгирования"""

        debug_log_write()
        warning_log_write()

    async def main(self):
        """Основная точка входа в бота и его запуск"""

        await self.catch_errors()
        # await self.init_models()
        await self.start_logging()
        await self.start()
        try:
            await self.dp.start_polling(self.bot, polling_timeout=100000)
        except Exception as e:
            logger.warning(str(e), traceback.format_exc())

    async def init_models(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)


if __name__ == '__main__':
    bot = MainBot()
    print('START BOT')
    asyncio.run(bot.main())
