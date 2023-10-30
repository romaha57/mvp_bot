from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.settings.service import SettingsService
from bot.settings.keyboards import BaseKeyboard
from bot.users.service import UserService


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = SettingsService()
        self.user_db = UserService()
        self.keyboard = BaseKeyboard()

    def handle(self):
        @self.router.message(Command('start'))
        async def start(message: Message, state: FSMContext):


            start_msg = await self.db.get_msg_by_key('intro')
            await message.answer(start_msg)

            # получаем промокод из сообщения пользователя
            promocode_in_msg = message.text.split()[1:]
            if promocode_in_msg:
                # проверяем наличие промокода в БД
                has_promocode = await self.db.check_promocode(promocode_in_msg[0])
                if has_promocode:
                    msg = await self.db.get_msg_by_key('have_promocode')

                    # сохраняем quiz_id у данного запроса
                    await state.update_data(quiz_id=has_promocode.quiz_id)
                    await state.update_data(promocode=has_promocode)

                    # сохраняем пользователя в БД
                    await self.user_db.get_or_create_user(
                        username=message.from_user.username,
                        tg_id=message.from_user.id,
                        bot_id=has_promocode.bot_id
                    )
                    kb = await self.keyboard.start_btn(has_promocode)
                else:
                    msg = await self.db.get_msg_by_key('bad_promocode')
                    kb = await self.keyboard.help_btn()

                await message.answer(msg, reply_markup=kb)

            else:
                msg = await self.db.get_msg_by_key('empty_promocode')
                await message.answer(msg)

        @self.router.message(Command('id'))
        async def get_tg_id(message: Message):
            """Отправляем telegram_id пользователя"""

            user_id = str(message.from_user.id)
            await message.answer(f'Ваш id - {user_id}')
