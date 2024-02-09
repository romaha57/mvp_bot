import traceback

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.handlers.base_handler import Handler
from bot.settings.keyboards import BaseKeyboard
from bot.users.keyboards import UserKeyboard
from bot.users.service import UserService
from bot.users.states import GeneratePromocodeState
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
        self.kb = UserKeyboard()
        self.base_kb = BaseKeyboard()

    def handle(self):
        @self.router.message(F.text == BUTTONS['REFERAL'])
        async def start_referal(message: Message):

            try:
                await message.answer(
                    MESSAGES['START_REFERAL'],
                    reply_markup=await self.base_kb.menu_btn()
                )

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.message(F.text == BUTTONS['BALANCE'])
        async def get_balance(message: Message):

            try:
                # user_account = await self.db.get_account_by_tg_id(message.from_user.id)
                #
                # # получаем баланс текущего пользователя
                # user_balance = await self.db.get_balance(
                #     account_id=user_account.id
                # )

                await message.answer(
                    MESSAGES['BALANCE'],
                    reply_markup=await self.base_kb.menu_btn()
                )

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.message(F.text == BUTTONS['PROMOCODES'])
        async def manager_panel(message: Message, state: FSMContext):
            try:
                await message.answer(
                    MESSAGES['MANAGER_PANEL'],
                    reply_markup=await self.kb.manager_btn()
                )
            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.message(F.text == BUTTONS['GENERATE_PROMOCODE'])
        async def start_generate_promocodes(message: Message, state: FSMContext):
            try:
                msg1 = await message.answer(
                    'Выберите роль',
                    reply_markup=await self.kb.choose_role_btn()
                )
                await state.set_state(GeneratePromocodeState.role)
                await state.update_data(msg1=msg1.message_id)

                menu_msg = await message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )
                await state.update_data(menu_msg=menu_msg.message_id)

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.callback_query(GeneratePromocodeState.role, F.data.startswith('role'))
        async def get_role_promocode(callback: CallbackQuery, state: FSMContext):
            """ Отлавливаем роль для промокода"""

            try:
                data = await state.get_data()
                role = callback.data.split('_')[1]

                # удаляем предыдущие кнопки
                await delete_messages(
                    data=data,
                    state=state,
                    src=callback
                )

                # сохраняем название роли
                await state.update_data(promocode_role=role)

                msg1 = await callback.message.answer(
                    'Выберите курс',
                    reply_markup=await self.kb.choose_course_btn()
                )
                await state.update_data(msg1=msg1.message_id)
                await state.set_state(GeneratePromocodeState.course)

                menu_msg = await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )
                await state.update_data(menu_msg=menu_msg.message_id)

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.callback_query(GeneratePromocodeState.course, F.data.startswith('course'))
        async def get_course_promocode(callback: CallbackQuery, state: FSMContext):
            try:
                data = await state.get_data()
                course = callback.data.split('_')[1]
                # удаляем предыдущие кнопки
                await delete_messages(
                    data=data,
                    state=state,
                    src=callback
                )

                # сохраняем название курса
                await state.update_data(promocode_course=course)

                msg1 = await callback.message.answer(
                    'Выберите квиз',
                    reply_markup=await self.kb.choose_quiz_btn()
                )
                await state.update_data(msg1=msg1.message_id)
                await state.set_state(GeneratePromocodeState.quiz)

                menu_msg = await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )
                await state.update_data(menu_msg=menu_msg.message_id)

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.callback_query(GeneratePromocodeState.quiz, F.data.startswith('quiz'))
        async def get_quiz_promocode(callback: CallbackQuery, state: FSMContext):
            try:
                data = await state.get_data()
                quiz = callback.data.split('_')[1]

                # удаляем предыдущие кнопки
                await delete_messages(
                    data=data,
                    state=state,
                    src=callback
                )

                # сохраняем название курса
                await state.update_data(promocode_quiz=quiz)
                # обновляем значение data, чтобы было значение promocode_quiz
                data = await state.get_data()

                # генерируем последовательность для промокода
                code = await generate_promocode()
                # получаем account пользователя
                account = await UserService.get_account_by_tg_id(callback.message.chat.id)

                # создаем промокод
                await self.db.create_promocode(
                    course_name=data['promocode_course'],
                    quiz_name=data['promocode_quiz'],
                    role=data['promocode_role'],
                    code=code,
                    account_id=account.id
                )

                msg1 = await callback.message.answer(
                    MESSAGES['CREATED_PROMOCODE'].format(
                        LINK + code
                    )
                )
                await state.update_data(msg1=msg1.message_id)
                await state.set_state(state=None)

                menu_msg = await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )
                await state.update_data(menu_msg=menu_msg.message_id)

            except Exception:
                logger.warning(traceback.format_exc())

        @self.router.message(F.text == BUTTONS['SEE_PROMOCODES'])
        async def see_generated_promocodes(message: Message, state: FSMContext):
            try:
                account = await self.db.get_account_by_tg_id(message.from_user.id)
                promocodes = await self.db.get_created_promocodes_by_manager(
                    account_id=account.id
                )
                answer = await format_created_promocodes_text(promocodes)

                await message.answer(
                    answer
                )

                menu_msg = await message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )
                await state.update_data(menu_msg=menu_msg.message_id)

            except Exception:
                logger.warning(traceback.format_exc())
