import traceback

from aiogram import Bot, F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.handlers.base_handler import Handler
from bot.quiz.keyboads import QuizKeyboard
from bot.quiz.service import QuizService
from bot.quiz.states import QuizState
from bot.settings.keyboards import BaseKeyboard
from bot.utils.answers import format_quiz_results, handle_quiz_answers
from bot.utils.buttons import BUTTONS
from bot.utils.delete_messages import delete_messages
from bot.utils.messages import MESSAGES


class QuizHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = QuizService()
        self.kb = QuizKeyboard()
        self.base_kb = BaseKeyboard()
        self.questions = None
        self.attempts_list = None
        self.index = None

    def handle(self):

        @self.router.message(F.text == BUTTONS['QUIZ'])
        async def quiz_menu(message: Message, state: FSMContext):
            """Отслеживание кнопки 'Тестирование'"""

            data = await state.get_data()

            # удаляем сообщения
            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            await message.answer(
                MESSAGES['QUIZ_SELECTION'],
                reply_markup=await self.kb.quiz_menu_btn()
            )



        @self.router.message(F.text == BUTTONS['START_QUIZ'])
        async def start_quiz(message: Message, state: FSMContext):
            """Обработка начала тестирования"""

            data = await state.get_data()
            user = await self.db.get_user_by_tg_id(message.from_user.id)

            # удаляем сообщения
            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            # получение тестирования
            quiz = await self.db.get_quiz_by_promocode(user.promocode_id)
            await message.answer(quiz.name)

            # если есть описание у квиза, то и его выводим
            if quiz.description:
                quiz_description_msg = await message.answer(quiz.description)

                await state.update_data(quiz_description_msg=quiz_description_msg.message_id)

            menu_msg = await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=await self.base_kb.menu_btn()
            )
            await state.update_data(menu_msg=menu_msg.message_id)

            # запись в БД о начале тестирования данным пользователем
            await self.db.create_attempt(
                quiz_id=quiz.id,
                tg_id=user.external_id

            )
            attempt = await self.db.get_last_attempt(user.id, quiz.id)

            await state.update_data(attempt_id=attempt.id)
            await state.update_data(quiz_id=quiz.id)

            # получаем вопросы для тестирования
            self.questions = await self.db.get_quiz_questions(quiz.id)

            question = self.questions.pop()
            msg = await message.answer(
                question.title,
                reply_markup=await self.kb.quiz_answers(question.id)
            )
            await state.update_data(delete_message_id=msg.message_id)
            await state.update_data(inline_msg=msg.message_thread_id)
            await state.update_data(question_title=question.title)
            await state.update_data(chat_id=msg.chat.id)

            # состояния на отлов ответа на этот вопрос
            await state.set_state(QuizState.answer)

        @self.router.callback_query(F.data.startswith('answer'), QuizState.answer)
        async def get_quiz_answer(callback: CallbackQuery, state: FSMContext):

            data = await state.get_data()

            # получаем ответ пользователя и создаем его в БД
            answer_id = callback.data.split('_')[1]
            answer = await self.db.create_answer(
                answer_id=answer_id,
                attempt_id=data['attempt_id'],
            )

            # берем вопросы из списка, пока они не закончатся
            try:
                question_title = data.get('question_title')
                await callback.message.edit_text(
                    text=f'{question_title}\n<b>Ответ: {answer}</b>',
                    inline_message_id=data.get('inline_msg'),
                    reply_markup=None
                )

                question = self.questions.pop()
                await callback.message.answer(
                    question.title,
                    reply_markup=await self.kb.quiz_answers(question.id)
                )
                await state.set_state(QuizState.answer)
                await state.update_data(question_title=question.title)
            except IndexError:
                # когда вопросов больше не будет, то удаляем состояние, но данные оставляем(нужен quiz_id)
                await state.set_state(state=None)

                await self.db.mark_quiz_completion(data['attempt_id'])

                # получаем финальное сообщение тестирования(о завершении)
                quiz = await self.db.get_quiz(data['quiz_id'])
                await callback.message.answer(
                    quiz.outro)

                # получаем все ответы для текущей попытки
                answers = await self.db.get_answers_by_attempt(data['attempt_id'])

                # получаем название функции обработки ответом пользователя на квиз
                calculate_func_name = quiz.function_name_to_calculate
                if calculate_func_name:
                    # обрабатываем ответы пользователя на квиз
                    result = await handle_quiz_answers(
                        answers=answers,
                        algorithm=calculate_func_name
                    )

                    # выводим подсчитанный ответ
                    await callback.message.answer(
                        result
                    )

                else:
                    # выводим ответы пользователя
                    result = await format_quiz_results(answers)
                    await callback.message.edit_text(
                        result
                    )

        @self.router.message(F.text == BUTTONS['RESULTS_QUIZ'])
        async def get_results_quiz(message: Message, state: FSMContext):
            """Получение результатов квиза"""

            data = await state.get_data()

            # удаляем сообщения
            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            # получаем все попытки текущего пользователя
            attempts = await self.db.get_quiz_attempts(
                tg_id=message.from_user.id
            )

            if attempts:
                self.attempts_list = attempts
                self.index = len(self.attempts_list) - 1
                attempt = self.attempts_list[self.index]
                answers = await self.db.get_answers_by_attempt(attempt.id)
                if answers:
                    result = await format_quiz_results(answers)
                    quiz_result_msg = await message.answer(
                        result,
                        reply_markup=await self.kb.switch_arrows_result_quiz_btn(self.attempts_list, self.index)
                    )

                    await state.update_data(quiz_result_msg=quiz_result_msg.message_id)
                    await state.update_data(quiz_result_chat_id=message.chat.id)

                else:
                    msg = await self.db.get_msg_by_key('empty_quiz_results')
                    await message.answer(
                        msg,
                        reply_markup=await self.base_kb.menu_btn()
                    )

            else:
                msg = await self.db.get_msg_by_key('empty_quiz_results')
                await message.answer(
                    msg,
                    reply_markup=await self.base_kb.menu_btn()
                )

        @self.router.message(or_f(F.text.startswith(BUTTONS['NEXT']), F.text.startswith(BUTTONS['PREVIOUS'])))
        async def get_other_result_quiz(message: Message, state: FSMContext):

            data = await state.get_data()

            # удаляем сообщения
            await delete_messages(
                src=message,
                data=data,
                state=state
            )
            # в зависимости какую кнопку нажал юзер(Следующая или Предыдущая)
            # получаем индекс для результата квиза
            if message.text == BUTTONS['NEXT']:
                self.index -= 1
            else:
                self.index += 1
            try:
                attempt = self.attempts_list[self.index]
                answers = await self.db.get_answers_by_attempt(attempt.id)
                if answers:
                    result = await format_quiz_results(answers)
                    quiz_result_msg = await message.answer(
                        result,
                        reply_markup=await self.kb.switch_arrows_result_quiz_btn(self.attempts_list, self.index)
                    )
                    await state.update_data(quiz_result_msg=quiz_result_msg.message_id)
                    await state.update_data(quiz_result_chat_id=message.chat.id)

            except IndexError:
                self.index = None
                await message.answer(
                    MESSAGES['MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )
