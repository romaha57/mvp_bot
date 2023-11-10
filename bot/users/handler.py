from aiogram import Bot, Router, F
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.settings.keyboards import BaseKeyboard
from bot.users.keyboards import UserKeyboard
from bot.users.service import UserService
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class UserHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = UserService()
        self.kb = UserKeyboard()
        self.base_kb = BaseKeyboard()

    def handle(self):
        @self.router.message(F.text == BUTTONS['REFERAL'])
        async def start_referal(message: Message):
            await message.answer(
                MESSAGES['START_REFERAL'],
                reply_markup=await self.base_kb.menu_btn()
            )

