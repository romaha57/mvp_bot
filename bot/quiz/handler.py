import datetime
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
from bot.test_promocode.keyboards import TestPromoKeyboard
from bot.test_promocode.utils import is_valid_test_promo
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
        self.test_promo_kb = TestPromoKeyboard()
        self.questions = None
        self.attempts_list = None
        self.index = None

    def handle(self):

        @self.router.message(F.text == BUTTONS['QUIZ'])
        async def quiz_menu(message: Message, state: FSMContext):
            """Отслеживание кнопки 'Тестирование'"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            # удаляем сообщения
            await delete_messages(
                src=message,
                data=data,
                state=state
            )
            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)
            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                await message.answer(
                    MESSAGES['YOUR_PROMOCODE_IS_EXPIRED'],
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

                await message.answer(
                    MESSAGES['QUIZ_SELECTION'],
                    reply_markup=await self.kb.quiz_menu_btn(promocode)
                )

        @self.router.message(F.text == BUTTONS['START_QUIZ'])
        async def start_quiz(message: Message, state: FSMContext):
            """Обработка начала тестирования"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            # удаляем сообщения
            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)
            user = await self.db.get_user_by_tg_id(message.chat.id)

            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                await message.answer(
                    MESSAGES['YOUR_PROMOCODE_IS_EXPIRED'],
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:

                if promocode.type_id == 3:
                    quizes_by_bot = await self.db.get_quizes_by_bot(message.chat.id)

                    quizes_by_db = await self.db.get_all_quizes()
                    all_quizes = list(set(quizes_by_bot + quizes_by_db))
                    all_quizes.sort(key=lambda elem: elem.get('id'))
                else:

                    quizes_by_promo = await self.db.get_quizes_by_promocode(message.chat.id)
                    quizes_by_bot = await self.db.get_quizes_by_bot(message.chat.id)
                    all_quizes = list(set(quizes_by_promo + quizes_by_bot))

                await message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )

                if len(all_quizes) > 1:
                    msg = await message.answer(
                        MESSAGES['CHOOSE_QUIZ'],
                        reply_markup=await self.kb.quizes_list_btn(all_quizes)
                    )
                    await state.set_state(QuizState.quiz)
                    await state.update_data(msg=msg.message_id)
                else:
                    quiz = all_quizes[0]
                    await message.answer(quiz.get('name'))
                    if quiz.description:
                        await message.answer(quiz.description)

                    # запись в БД о начале тестирования данным пользователем
                    await self.db.create_attempt(
                        quiz_id=quiz.get('id'),
                        user=user

                    )

                    await state.set_state(QuizState.answer)

                    self.questions = await self.db.get_quiz_questions(quiz.get('id'))
                    question = self.questions.pop()
                    msg = await message.answer(
                        question.title,
                        reply_markup=await self.kb.quiz_answers(question.id)
                    )

                    await state.update_data(quiz_id=quiz.get('id'))
                    await state.update_data(question_title=question.title)
                    await state.update_data(inline_msg=msg.message_thread_id)

        @self.router.callback_query(QuizState.quiz, F.data.startswith('quiz'))
        async def get_quiz(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages(
                data=data,
                state=state,
                src=callback.message
            )

            user = await self.db.get_user_by_tg_id(callback.message.chat.id)
            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
            if promocode.end_at <= datetime.datetime.now():
                courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
                await callback.message.answer(
                    MESSAGES['YOUR_PROMOCODE_IS_EXPIRED'],
                    reply_markup=await self.base_kb.start_btn(courses_and_quizes)
                )
            else:
                if promocode.is_test and not is_valid_test_promo(user):
                    await callback.message.answer(
                        MESSAGES['END_TEST_PERIOD'],
                        reply_markup=await self.test_promo_kb.test_promo_menu()
                    )
                else:
                    quiz_id = callback.data.split('_')[-1]
                    user = await self.db.get_user_by_tg_id(callback.message.chat.id)
                    await self.db.create_attempt(
                        quiz_id=quiz_id,
                        user=user

                    )

                    await state.set_state(QuizState.answer)

                    self.questions = await self.db.get_quiz_questions(quiz_id)
                    question = self.questions.pop()
                    msg = await callback.message.answer(
                        question.title,
                        reply_markup=await self.kb.quiz_answers(question.id)
                    )

                    await state.update_data(quiz_id=quiz_id)
                    await state.update_data(question_title=question.title)
                    await state.update_data(inline_msg=msg.message_thread_id)
                    await state.update_data(msg=msg.message_id)

        @self.router.callback_query(F.data.startswith('answer'), QuizState.answer)
        async def get_quiz_answer(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            quiz_id = data.get('quiz_id')
            attempt = await self.db.get_last_attempt(
                tg_id=callback.message.chat.id,
                quiz_id=quiz_id
            )
            promocode = await self.db.get_promocode_by_tg_id(callback.message.chat.id)
            # получаем ответ пользователя и создаем его в БД
            answer_id = callback.data.split('_')[1]
            answer = await self.db.create_answer(
                answer_id=answer_id,
                attempt_id=attempt.id,
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
                msg = await callback.message.answer(
                    question.title,
                    reply_markup=await self.kb.quiz_answers(question.id)
                )
                await state.set_state(QuizState.answer)
                await state.update_data(question_title=question.title)
                await state.update_data(msg=msg.message_id)
            except IndexError:
                # когда вопросов больше не будет, то удаляем состояние, но данные оставляем(нужен quiz_id)
                await state.set_state(state=None)

                await self.db.mark_quiz_completion(attempt.id)

                # получаем финальное сообщение тестирования(о завершении)
                quiz = await self.db.get_quiz(quiz_id)
                await callback.message.answer(
                    quiz.outro)

                # получаем все ответы для текущей попытки
                answers = await self.db.get_answers_by_attempt(attempt.id)

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
                        result,
                        reply_markup=await self.kb.quiz_menu_btn(promocode)
                    )

                else:
                    # выводим ответы пользователя
                    result = await format_quiz_results(answers)
                    await callback.message.answer(
                        result,
                        reply_markup=await self.kb.quiz_menu_btn(promocode)
                    )

        @self.router.message(F.text == BUTTONS['RESULTS_QUIZ'])
        async def get_results_quiz(message: Message, state: FSMContext):
            """Получение результатов квиза"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            # удаляем сообщения
            await delete_messages(
                src=message,
                data=data,
                state=state
            )

            user = await self.db.get_user_by_tg_id(message.chat.id)
            promocode = await self.db.get_promocode_by_tg_id(message.chat.id)
            attempts = await self.db.get_quiz_attempts(
                user=user
            )

            if attempts:
                self.attempts_list = attempts
                self.index = len(self.attempts_list) - 1
                attempt = self.attempts_list[self.index]
                answers = await self.db.get_answers_by_attempt(attempt.id)
                if answers:
                    result = await format_quiz_results(answers)
                    await message.answer(
                        result,
                        reply_markup=await self.kb.switch_arrows_result_quiz_btn(self.attempts_list, self.index)
                    )

                else:
                    msg = await self.db.get_msg_by_key('empty_quiz_results')
                    await message.answer(
                        msg,
                        reply_markup=await self.kb.quiz_menu_btn(promocode)
                    )

            else:
                msg = await self.db.get_msg_by_key('empty_quiz_results')
                await message.answer(
                    msg,
                    reply_markup=await self.kb.quiz_menu_btn(promocode)
                )

        @self.router.message(or_f(F.text.startswith(BUTTONS['NEXT']), F.text.startswith(BUTTONS['PREVIOUS'])))
        async def get_other_result_quiz(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
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
                    await message.answer(
                        result,
                        reply_markup=await self.kb.switch_arrows_result_quiz_btn(self.attempts_list, self.index)
                    )

            except IndexError:
                self.index = None
                await message.answer(
                    MESSAGES['MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )
