from sqlalchemy import select, insert, CursorResult, desc, update

from bot.db_connect import async_session
from bot.services.base_service import BaseService
from bot.quiz.models import Quizes, QuizQuestions, QuizQuestionOptions, QuizAttempts, QuizAttemptStatuses, QuizAnswers
from bot.users.models import Promocodes
from bot.users.service import UserService


class QuizService(BaseService):
    model = Quizes

    @classmethod
    async def get_quiz_questions(cls, quiz_id: int, offset: int = None):
        """"Поучение всех вопросов определённого тестирования"""

        async with async_session() as session:
            query = select(QuizQuestions).filter_by(quiz_id=quiz_id).order_by(desc('id'))
            result = await session.execute(query)

            return result.scalars().all()



    @classmethod
    async def get_quiz(cls, promocode_id: int):
        """Получение тестирования по его id"""

        promocode = await cls.get_promocode(promocode_id)

        async with async_session() as session:
            query = select(Quizes).join(Promocodes, Promocodes.quiz_id == Quizes.id).where(Promocodes.id==promocode_id)
            result = await session.execute(query)

            return result.scalars().one()

    @classmethod
    async def get_quiz_answers(cls, question_id: int):
        """Получение вариантов ответа для определённого вопроса"""

        async with async_session() as session:
            query = select(QuizQuestionOptions).filter_by(question_id=question_id)
            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_answer_by_id(cls, answer_id: str):
        """Получение текста ответа по его id"""

        async with async_session() as session:
            query = select(QuizQuestionOptions.title).filter_by(id=answer_id)
            result = await session.execute(query)

            return result.scalars().one()

    @classmethod
    async def create_attempt(cls, quiz_id: int, tg_id: int):
        """Создание попытки прохождения теста"""

        user = await cls.get_user_by_tg_id(tg_id)
        status = await cls.get_attempt_status('В процессе')
        async with async_session() as session:
            query = insert(QuizAttempts).values(
                quiz_id=quiz_id,
                user_id=user.id,
                status_id=status.id
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def mark_quiz_completion(cls, attempt_id: int):
        """Отмечаем статус попытки на 'завершен' """

        status = await cls.get_attempt_status('Завершен')
        async with async_session() as session:
            query = update(QuizAttempts).where(QuizAttempts.id==attempt_id).values(status_id=status.id)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_attempt_status(cls, status_name: str):
        """Получение статуса попытки прохождения тестирования"""

        async with async_session() as session:
            query = select(QuizAttemptStatuses).filter_by(name=status_name)
            result = await session.execute(query)

            return result.scalars().one()

    @classmethod
    async def create_answer(cls, answer_id: str, attempt_id: int, answer: str):
        async with async_session() as session:
            query = insert(QuizAnswers).values(
                option_id=answer_id,
                attempt_id=attempt_id,
                details=answer
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_last_attempt(cls, user_id: int, quiz_id: int):
        async with async_session() as session:
            query = select(QuizAttempts).filter_by(user_id=user_id, quiz_id=quiz_id).order_by(desc('id'))
            result: CursorResult = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_attempts(cls, tg_id: int):
        user = await cls.get_user_by_tg_id(tg_id)

        async with async_session() as session:
            query = select(QuizAttempts).filter_by(
                user_id=user.id
            )
            result: CursorResult = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_answers_by_attempt(cls, attempt_id: int):
        async with async_session() as session:
            query = select(QuizAnswers).filter_by(
                attempt_id=attempt_id
            )
            result: CursorResult = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_question_by_option(cls, option_id: str):
        """Получаем навзвание вопросов по id варианта ответа"""

        async with async_session() as session:

            q = select(
                QuizQuestions.title.label('question_title')).join(
                QuizQuestionOptions, QuizQuestions.id == QuizQuestionOptions.question_id
            ).where(
                QuizQuestionOptions.id == option_id
            )

            res = await session.execute(q)

            return res.scalars().first()

