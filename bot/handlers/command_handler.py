import traceback

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.courses.service import CourseService
from bot.handlers.base_handler import Handler
from bot.settings.keyboards import BaseKeyboard
from bot.settings.service import SettingsService
from bot.users.service import UserService
from loguru import logger


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = SettingsService()
        self.user_db = UserService()
        self.course_db = CourseService()
        self.keyboard = BaseKeyboard()

    def handle(self):
        @self.router.message(Command('start'))
        async def start(message: Message, state: FSMContext):
            """Отлов команды /start"""

            try:
                start_msg = await self.db.get_msg_by_key('intro')
                await message.answer(start_msg)

                await state.update_data(chat_id=message.chat.id)

                # получаем промокод из сообщения пользователя
                promocode_in_msg = message.text.split()[1:]
                logger.debug(f"Пользователь {message.from_user.id} ввел промокод {promocode_in_msg}")
                if promocode_in_msg:
                    # проверяем наличие промокода в БД
                    promocode = await self.db.check_promocode(promocode_in_msg[0])
                    if promocode.actual:
                        msg = await self.db.get_msg_by_key('have_promocode')
                        logger.debug(f"Пользователь {message.from_user.id} активировал промокод {promocode.code}")

                        # сохраняем промокод в состояние
                        await state.update_data(promocode_id=promocode.id)

                        # увеличиваем счетчик активированных пользователей на этом промокоде
                        await self.db.increment_count_promocode(
                            promocode
                        )

                        # сохраняем пользователя в БД
                        await self.user_db.get_or_create_user(
                            username=message.from_user.username,
                            tg_id=message.chat.id,
                            bot_id=promocode.bot_id,
                            first_name=message.from_user.first_name,
                            last_name=message.from_user.last_name
                        )
                        kb = await self.keyboard.start_btn(promocode)

                        user = await self.db.get_user_by_tg_id(message.from_user.id)

                        # добавляем флаг у юзера, чтобы ему показывать стартовое видео курса
                        await self.course_db.mark_user_show_course_description(user, True)
                    else:
                        msg = await self.db.get_msg_by_key('bad_promocode')
                        kb = await self.keyboard.help_btn()

                    await message.answer(msg, reply_markup=kb)
                    await self.user_db.add_promocode_to_user(
                        tg_id=message.from_user.id,
                        promocode_id=promocode.id
                    )

                else:
                    msg = await self.db.get_msg_by_key('empty_promocode')
                    await message.answer(msg)

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.message(Command('id'))
        async def get_tg_id(message: Message):
            """Отправляем telegram_id пользователя"""

            try:

                user_id = str(message.from_user.id)
                await message.answer(f'Ваш id - <b>{user_id}</b>')
            except Exception:
                logger.warning(traceback.format_exc())
