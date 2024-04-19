import hashlib
import traceback
import uuid

import segno
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile
from loguru import logger

from bot.courses.keyboards import CourseKeyboard
from bot.courses.service import CourseService
from bot.courses.states import CourseChooseState
from bot.handlers.base_handler import Handler
from bot.quiz.keyboads import QuizKeyboard
from bot.quiz.service import QuizService
from bot.quiz.states import QuizState
from bot.settings.keyboards import BaseKeyboard
from bot.users.keyboards import UserKeyboard
from bot.users.service import UserService
from bot.users.states import GeneratePromocodeState, UserReport
from bot.utils.answers import (format_created_promocodes_text,
                               generate_promocode)
from bot.utils.buttons import BUTTONS
from bot.utils.constants import LINK
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class UserHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = UserService()
        self.quiz_db = QuizService()
        self.course_db = CourseService()
        self.kb = UserKeyboard()
        self.base_kb = BaseKeyboard()
        self.quiz_kb = QuizKeyboard()
        self.course_kb = CourseKeyboard()

    def handle(self):
        @self.router.message(F.text == BUTTONS['REFERAL'])
        async def start_referal(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            account = await self.db.get_account_by_tg_id(message.chat.id)
            account_id = str(account.id).encode()
            referal_code = hashlib.md5(account_id).hexdigest()[:7]
            referal_link = f't.me/Realogika_bot?start={referal_code}'

            qr_path = f'/app/static/qr/qr_{referal_code}.png'
            qr_code = segno.make(referal_link, micro=False)
            qr_code.save(qr_path, scale=5)
            qrcode = FSInputFile(qr_path)
            logger.debug(f"Пользователь {message.from_user.id}, {qr_path} === {qrcode}")

            count_users = await self.db.get_connected_users(account.id)
            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)
            courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)

            await message.bot.send_document(
                chat_id=data.get('chat_id'),
                document=qrcode
            )

            await message.answer(
                MESSAGES['START_REFERAL'].format(
                    referal_link,
                    count_users
                ),
                reply_markup=await self.base_kb.start_btn(courses_and_quizes)
            )
            await self.db.create_promocode(
                name=f'{account.first_name} {account.last_name}/ {account.email}',
                code=referal_code,
                account_id=account.id
            )

        @self.router.message(F.text == BUTTONS['BALANCE'])
        async def get_balance(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages(
                src=message,
                data=data,
                state=state
            )
            # user_account = await self.db.get_account_by_tg_id(message.from_user.id)
            #
            # # получаем баланс текущего пользователя
            # user_balance = await self.db.get_balance(
            #     account_id=user_account.id
            # )

            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)
            courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
            await message.answer(
                MESSAGES['BALANCE'],
                reply_markup=await self.base_kb.start_btn(courses_and_quizes)
            )

        @self.router.message(F.text == BUTTONS['OWNER_QUIZ'])
        async def get_owner_quiz(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)
            await message.answer(
                MESSAGES['QUIZ_SELECTION'],
                reply_markup=await self.quiz_kb.quiz_menu_btn(promocode)
            )

        @self.router.message(F.text == BUTTONS['OWNER_EDUCATION'])
        async def start_test_education(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            courses_by_bot = await self.course_db.get_courses_by_bot(message.chat.id)
            courses_by_db = await self.course_db.get_all_courses()
            all_courses = list(set(courses_by_bot + courses_by_db))
            all_courses.sort(key=lambda elem: elem.get('id'))

            msg = await message.answer(
                MESSAGES['CHOOSE_COURSE'],
                reply_markup=await self.course_kb.courses_btn(all_courses)
            )

            await state.update_data(msg=msg.message_id)
            await state.set_state(CourseChooseState.course)

            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=await self.base_kb.menu_btn()
            )