import datetime
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
from bot.test_promocode.keyboards import TestPromoKeyboard
from bot.test_promocode.utils import is_valid_test_promo
from bot.users.keyboards import UserKeyboard
from bot.users.service import UserService
from bot.users.states import GeneratePromocodeState, UserReport, Politics
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
        self.test_promo_kb = TestPromoKeyboard()

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
            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                msg_text = await self.db.get_msg_by_key('YOUR_PROMOCODE_IS_EXPIRED')
                await message.answer(
                    msg_text,
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:
                await self.db.create_promocode(
                    name=f'{account.first_name} {account.last_name}/ {account.email}',
                    code=referal_code,
                    account_id=account.id,
                )

                if promocode.type_id == 3:
                    kb = await self.base_kb.start_btn(promocode)

                else:
                    courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                    kb = await self.base_kb.start_btn(courses_and_quizes)

                await message.bot.send_document(
                    chat_id=data.get('chat_id'),
                    document=qrcode
                )

                msg_text = await self.db.get_msg_by_key('START_REFERAL')
                await message.answer(
                    msg_text.format(
                        referal_link,
                        count_users
                    ),
                    reply_markup=kb
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
            msg_text = await self.db.get_msg_by_key('BALANCE')
            await message.answer(
                msg_text,
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
            msg_text = await self.db.get_msg_by_key('QUIZ_SELECTION')
            await message.answer(
                msg_text,
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
            all_courses.sort(key=lambda elem: elem.get('order_num'))

            msg_text = await self.db.get_msg_by_key('CHOOSE_COURSE')
            msg = await message.answer(
                msg_text,
                reply_markup=await self.course_kb.courses_btn(all_courses)
            )

            await state.update_data(msg=msg.message_id)
            await state.set_state(CourseChooseState.course)

            msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
            await message.answer(
                msg_text,
                reply_markup=await self.base_kb.menu_btn()
            )

        @self.router.message(Politics.accept)
        async def empty_answer(message: Message):
            pass

        @self.router.callback_query(F.data.startswith('accept_politics'), Politics.accept)
        async def accept_politics(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages(
                src=callback.message,
                data=data,
                state=state
            )

            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
            user = await self.db.get_user_by_tg_id(callback.message.chat.id)
            await self.db.accept_politics(callback.message.chat.id)

            if promocode.is_test:
                if is_valid_test_promo(user):
                    msg_text = await self.db.get_msg_by_key('TEST_PROMO_MENU')
                    await callback.message.answer(
                        msg_text,
                        reply_markup=await self.test_promo_kb.test_promo_menu()
                    )

                else:
                    msg_text = await self.db.get_msg_by_key('END_TEST_PERIOD')
                    await callback.message.answer(
                        msg_text,
                        reply_markup=await self.test_promo_kb.test_promo_menu()
                    )
                    await state.set_state(state=None)

            else:
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                msg_text = await self.db.get_msg_by_key('MENU')
                await callback.message.answer(
                    msg_text,
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
