import datetime
import traceback

import pytz
from aiogram import Bot, Router
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
from bot.users.states import Anketa
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

            await state.update_data(chat_id=message.chat.id)

            promocode_in_msg = message.text.split()[1:]
            logger.debug(f"Пользователь {message.chat.id} ввел промокод {promocode_in_msg}")
            if promocode_in_msg:
                promocode = await self.db.check_promocode(promocode_in_msg[0])
                if promocode and promocode.actual:
                    courses_by_promo = await self.db.get_courses_by_promo(promocode.id)
                    
                    if courses_by_promo:
                        courses_titles = '\n'.join([f" - {course.get('title')}" for course in courses_by_promo])
                        await message.answer(
                            MESSAGES['START_PROMOCODE'].format(
                                courses_titles
                            )
                        )
                    elif promocode.is_test:
                        await message.answer(
                            MESSAGES['GO_TO_TEST_PROMOCODE']
                        )
                    else:
                        await message.answer(
                            MESSAGES['START_PROMOCODE_OWNER']
                        )
                    logger.debug(f"Пользователь {message.from_user.id} активировал промокод {promocode.code}")

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

                    await self.db.add_promocode_to_user(
                        tg_id=message.chat.id,
                        promocode_id=promocode.id
                    )

                    user_account = await self.db.get_account_by_tg_id(message.chat.id)

                    if promocode.account_id:
                        await self.db.add_promocode_partners(
                            promocode=promocode,
                            user=user_account
                        )

                    user = await self.db.get_user_by_tg_id(message.chat.id)
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
                            await message.answer(
                                MESSAGES['GO_TO_TEST_PROMOCODE'],
                                reply_markup=await self.test_promo_kb.test_promo_menu())

                        else:
                            courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                            await self.user_db.add_promocode_to_user(
                                tg_id=message.from_user.id,
                                promocode_id=promocode.id
                            )
                            await message.answer(
                                MESSAGES['MENU'],
                                reply_markup=await self.kb.start_btn(courses_and_quizes))

                else:
                    msg = await self.db.get_msg_by_key('bad_promocode')
                    kb = await self.kb.help_btn()

                    await message.answer(msg, reply_markup=kb)

            else:
                msg = await self.db.get_msg_by_key('empty_promocode')
                await message.answer(msg)

        async def get_user_answers_for_anketa(message: Message, state: FSMContext, questions: list[dict]):
            await message.answer(
                MESSAGES['START_ANKETA']
            )

            self.anketa_questions = questions
            first_question = self.anketa_questions.pop()
            await message.answer(
                MESSAGES['ANKETA_QUESTION'].format(
                    first_question.get('title')
                )
            )
            await state.update_data(anketa_question_id=first_question.get('id'))
            await state.set_state(Anketa.answer)

            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=await self.kb.menu_btn()
            )

        @self.router.message(Command('id'))
        async def get_tg_id(message: Message):
            """Отправляем telegram_id пользователя"""

            user_id = str(message.from_user.id)
            await message.answer(f'Ваш id - <b>{user_id}</b>')

