import datetime
import traceback

import pytz
import requests
from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.courses.service import CourseService
from bot.handlers.base_handler import Handler
from bot.settings.keyboards import BaseKeyboard
from bot.settings.service import SettingsService
from bot.test_promocode.keyboards import TestPromoKeyboard
from bot.users.service import UserService
from bot.users.states import Anketa, Politics
from bot.utils.answers import check_user_anket
from bot.utils.messages import MESSAGES


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = SettingsService()
        self.user_db = UserService()
        self.course_db = CourseService()
        self.kb = BaseKeyboard()
        self.test_promo_kb = TestPromoKeyboard()

    def handle(self):
        @self.router.message(Command('start'))
        async def start(message: Message, state: FSMContext):
            """Отлов команды /start"""

#             b = {
#                 "chat_id": '6718255302',
#                 "text": """
#                 <b>Переход в Бот Собственника</b>
# Уважаемые партнеры, для вашего удобства мы сделали доступным переход в бот прямо из этого чата. Нажимая на кнопку-переход у вас откроется бот “Реалогика” на активном курсе.
# Теперь переходить в бот к актуальным урокам будет проще!
#
#                 """,
#                 "parse_mode": "html",
#                 "reply_markup": {
#                     "inline_keyboard": [
#                         [
#                             {
#                                 "text": 'Бот Реалогика',
#                                 "callback_data": "none",
#                                 "url": "https://t.me/Realogika_bot"
#                             }
#                         ]
#                     ]
#                 }
#             }
#             r = requests.post(f'https://api.telegram.org/bot6350582410:AAFs2em1RzrjhIKuUmkvLOecCvTOqC193Bg/sendMessage', json=b)
#             print(r.json())
#
#             b = {
#                 "chat_id": '@ecomtesttest',
#                 "text": """
#                              <b>Переход в Бот Реалогика</b>
# Для вашего удобства мы сделали доступным переход в бот прямо из этого чата. Нажимая на кнопку-переход у вас откроется бот “Реалогика” на активном курсе.
# Теперь переходить в бот к актуальным урокам будет проще!
#
#                             """,
#                 "parse_mode": "html",
#                 "reply_markup": {
#                     "inline_keyboard": [
#                         [
#                             {
#                                 "text": 'Бот Реалогика',
#                                 "callback_data": "none",
#                                 "url": "https://t.me/Realogika_bot"
#                             }
#                         ]
#                     ]
#                 }
#             }
#             r = requests.post(f'https://api.telegram.org/bot6350582410:AAFs2em1RzrjhIKuUmkvLOecCvTOqC193Bg/sendMessage',
#                               json=b)
#             print(r.json())











            await state.update_data(chat_id=message.chat.id)
            promocode_in_msg = message.text.split()[1:]
            logger.debug(f"Пользователь {message.chat.id} ввел промокод {promocode_in_msg}")

            await self.db.delete_all_from_course_bot()

            # -------------------- Если пользотваель ввел /start без промокода, но у него уже есть промокодов в БД

            promocode_from_db = await self.db.get_promocode_by_tg_id(message.chat.id)
            if not promocode_in_msg and promocode_from_db:
                if promocode_from_db.type_id == 3:
                    msg_text = await self.db.get_msg_by_key('START_PROMOCODE_OWNER')
                    await message.answer(
                        msg_text,
                        reply_markup=await self.kb.start_btn(promocode_from_db))

                elif promocode_from_db.is_test:
                    msg_text = await self.db.get_msg_by_key('GO_TO_TEST_PROMOCODE')
                    await message.answer(
                        msg_text,
                        reply_markup=await self.test_promo_kb.test_promo_menu())

                else:
                    courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode_from_db.id)
                    msg_text = await self.db.get_msg_by_key('MENU')
                    await message.answer(
                        msg_text,
                        reply_markup=await self.kb.start_btn(courses_and_quizes))

            # ------------------------------------------------------------------------------------------------------
            else:
                if promocode_in_msg:
                    promocode = await self.db.check_promocode(promocode_in_msg[0])
                    if promocode and promocode.actual:
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

                        user = await self.db.get_user_by_tg_id(message.chat.id)

                        if promocode.is_test and user.promocode_id and not promocode_from_db.is_test:
                            courses_and_quizes = await self.db.get_promocode_courses_and_quizes(user.promocode_id)
                            msg_text = await self.db.get_msg_by_key('MENU')
                            await message.answer(
                                msg_text,
                                reply_markup=await self.kb.start_btn(courses_and_quizes))

                        else:
                            await self.db.add_promocode_to_user(
                                tg_id=message.chat.id,
                                promocode_id=promocode.id
                            )
                            courses_by_promo = await self.db.get_courses_by_promo(promocode.id)
                            if courses_by_promo:
                                courses_titles = '\n'.join([f" - {course.get('title')}" for course in courses_by_promo])
                                msg_text = await self.db.get_msg_by_key('START_PROMOCODE')
                                await message.answer(
                                    msg_text.format(
                                        courses_titles
                                    )
                                )

                            logger.debug(f"Пользователь {message.chat.id} активировал промокод {promocode.code}")

                            user_account = await self.db.get_account_by_tg_id(message.chat.id)
                            if promocode.account_id and user_account.id != promocode.account_id:
                                await self.db.add_promocode_partners(
                                    promocode=promocode,
                                    user=user_account
                                )

                            if user.accept_politics:
                                anketa_questions = await check_user_anket(
                                    message=message,
                                    user=user
                                )
                                if anketa_questions:
                                    await get_user_answers_for_anketa(
                                        message=message,
                                        state=state,
                                        questions=anketa_questions
                                    )

                                else:

                                    if promocode.is_test:
                                        now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
                                        user = await self.db.get_user_by_tg_id(message.chat.id)
                                        await self.db.set_start_and_end_time_test_promo(
                                            now=now,
                                            promocode=promocode,
                                            user=user
                                        )
                                        msg_text = await self.db.get_msg_by_key('GO_TO_TEST_PROMOCODE')
                                        await message.answer(
                                            msg_text,
                                            reply_markup=await self.test_promo_kb.test_promo_menu())

                                    elif promocode.type_id == 3:
                                        msg_text = await self.db.get_msg_by_key('START_PROMOCODE_OWNER')
                                        await message.answer(
                                            msg_text,
                                            reply_markup=await self.kb.start_btn(promocode))

                                    else:
                                        courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                                        await self.user_db.add_promocode_to_user(
                                            tg_id=message.chat.id,
                                            promocode_id=promocode.id
                                        )
                                        msg_text = await self.db.get_msg_by_key('MENU')
                                        await message.answer(
                                            msg_text,
                                            reply_markup=await self.kb.start_btn(courses_and_quizes))
                            else:
                                msg_text = await self.db.get_msg_by_key('ACCEPT_POLITICS')
                                msg = await message.answer(
                                    msg_text,
                                    reply_markup=await self.kb.politics_btn()
                                )
                                await state.set_state(Politics.accept)
                                await state.update_data(msg=msg.message_id)
                    else:
                        msg = await self.db.get_msg_by_key('bad_promocode')
                        kb = await self.kb.help_btn()

                        await message.answer(msg, reply_markup=kb)

                else:
                    msg = await self.db.get_msg_by_key('empty_promocode')
                    await message.answer(msg)

        async def get_user_answers_for_anketa(message: Message, state: FSMContext, questions: list[dict]):
            msg_text = await self.db.get_msg_by_key('START_ANKETA')
            await message.answer(
                msg_text
            )

            self.anketa_questions = questions
            first_question = self.anketa_questions.pop()
            msg_text = await self.db.get_msg_by_key('ANKETA_QUESTION')
            await message.answer(
                msg_text.format(
                    first_question.get('title')
                )
            )
            await state.update_data(anketa_question_id=first_question.get('id'))
            await state.set_state(Anketa.answer)

            msg_text = await self.db.get_msg_by_key('GO_TO_MENU')
            await message.answer(
                msg_text,
                reply_markup=await self.kb.menu_btn()
            )

        @self.router.message(Command('id'))
        async def get_tg_id(message: Message):
            """Отправляем telegram_id пользователя"""

            user_id = str(message.chat.id)
            await message.answer(f'Ваш id - <b>{user_id}</b>')
