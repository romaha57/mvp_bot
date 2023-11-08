from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.base_handler import Handler
from bot.quiz.keyboads import QuizKeyboard
from bot.quiz.service import QuizService
from bot.quiz.states import QuizState
from bot.settings.keyboards import BaseKeyboard
from bot.utils.answers import format_quiz_results
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class QuizHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.db = QuizService()
        self.kb = QuizKeyboard()
        self.base_kb = BaseKeyboard()
        self.questions = None

    def handle(self):

        @self.router.message(F.text == BUTTONS['QUIZ'])
        async def start_quiz(message: Message, state: FSMContext):
            """Обработка начала тестирования"""

            user = await self.db.get_user_by_tg_id(message.from_user.id)

            # стартовое сообщение при тестировании
            start_msg = await self.db.get_msg_by_key('start_quiz')
            await message.answer(start_msg)

            # получение тестирования
            quiz = await self.db.get_quiz(user.promocode_id)
            await message.answer(quiz.name)

            attempt = await self.db.get_last_attempt(user.id, quiz.id)
            if not attempt:
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
            await state.update_data(delete_chat_id=msg.chat.id)

            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=await self.base_kb.menu_btn()
            )
            # состояния на отлов ответа на этот вопрос
            await state.set_state(QuizState.answer)

        @self.router.callback_query(F.data.startswith('answer'), QuizState.answer)
        async def get_quiz_answer(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            # получаем ответ пользователя и создаем его в БД
            answer_id = callback.data.split('_')[1]
            await self.db.create_answer(
                answer_id=answer_id,
                attempt_id=data['attempt_id'],
            )

            # берем вопросы из списка, пока они не закончатся
            try:
                question = self.questions.pop()
                await callback.message.edit_text(
                    question.title,
                    reply_markup=await self.kb.quiz_answers(question.id)
                )
                await state.set_state(QuizState.answer)
            except IndexError:
                # когда вопросов больше не будет, то удаляем состояние, но данные оставляем(нужен quiz_id)
                await state.set_state(state=None)

                await self.db.mark_quiz_completion(data['attempt_id'])

                # получаем финальное сообщение тестирования(о завершении)
                quiz = await self.db.get_quiz(data['quiz_id'])
                await callback.message.edit_text(
                    quiz.outro)
                await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=await self.base_kb.menu_btn()
                )


        @self.router.message(F.text == BUTTONS['RESULTS_QUIZ'])
        async def get_results_quiz(message: Message):

            # получаем все попытки текущего пользователя
            attempts = await self.db.get_attempts(
                tg_id=message.from_user.id
            )
            if attempts:

                for attempt in attempts:
                    answers = await self.db.get_answers_by_attempt(attempt.id)
                    result = await format_quiz_results(answers)
                    await message.answer(
                        result,
                        reply_markup=await self.base_kb.menu_btn()
                    )

            else:
                msg = await self.db.get_msg_by_key('empty_quiz_results')
                await message.answer(
                    msg,
                    reply_markup=await self.base_kb.menu_btn()
                )
