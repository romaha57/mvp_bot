from sqlalchemy import desc, insert, select, update

from bot.db_connect import async_session
from bot.quiz.models import (QuizAnswers, QuizAttempts, QuizAttemptStatuses,
                             Quizes, QuizQuestionOptions, QuizQuestions, QuizBots)
from bot.services.base_service import BaseService, Singleton
from bot.users.models import Promocodes, PromocodeQuizes, Users


class QuizService(BaseService, metaclass=Singleton):
    model = Quizes

    @classmethod
    async def get_all_quizes(cls):
        """Получение всех квизов из БД"""

        async with async_session() as session:
            query = select(Quizes.id, Quizes.name, Quizes.description)
            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def get_quiz_questions(cls, quiz_id: str) -> list[QuizQuestions]:
        """"Поучение всех вопросов определённого тестирования"""

        async with async_session() as session:
            query = select(QuizQuestions).filter_by(quiz_id=quiz_id).order_by(desc('id'))
            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_quizes_by_promocode(cls, tg_id: int):
        """Получение тестирования по его id промокода"""

        async with async_session() as session:
            query = select(Quizes.id, Quizes.name, Quizes.description). \
                join(PromocodeQuizes, PromocodeQuizes.quiz_id == Quizes.id). \
                join(Users, Users.promocode_id == PromocodeQuizes.promocode_id). \
                where(Users.external_id == tg_id)
            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def get_quizes_by_bot(cls, tg_id: int):
        async with async_session() as session:
            query = select(Quizes.id, Quizes.name, Quizes.description). \
                join(QuizBots, Quizes.id == QuizBots.quiz_id). \
                join(Users, Users.bot_id == QuizBots.bot_id). \
                where(Users.external_id == tg_id)
            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def get_quiz(cls, quiz_id: int) -> Quizes:
        """Получение тестирования по его id"""

        async with async_session() as session:
            query = select(Quizes).where(Quizes.id == quiz_id)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_quiz_answers(cls, question_id: int) -> list[QuizQuestionOptions]:
        """Получение вариантов ответа для определённого вопроса"""

        async with async_session() as session:
            query = select(QuizQuestionOptions).filter_by(question_id=question_id)
            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_answer_by_id(cls, answer_id: str) -> str:
        """Получение текста ответа по его id"""

        async with async_session() as session:
            query = select(QuizQuestionOptions.title).filter_by(id=answer_id)
            result = await session.execute(query)

            return result.scalars().one()

    @classmethod
    async def create_attempt(cls, quiz_id: str, user: Users) -> None:
        """Создание попытки прохождения теста"""

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
            query = update(QuizAttempts).\
                where(QuizAttempts.id == attempt_id).\
                values(status_id=status.id)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_attempt_status(cls, status_name: str) -> QuizAttemptStatuses:
        """Получение статуса попытки прохождения тестирования"""

        async with async_session() as session:
            query = select(QuizAttemptStatuses).filter_by(name=status_name)
            result = await session.execute(query)

            return result.scalars().one()

    @classmethod
    async def create_answer(cls, answer_id: str, attempt_id: int):
        async with async_session() as session:
            query = insert(QuizAnswers).\
                values(
                option_id=answer_id,
                attempt_id=attempt_id,
            )
            await session.execute(query)

            query = select(QuizQuestionOptions.title).select_from(QuizQuestionOptions).\
                join(QuizAnswers, QuizQuestionOptions.id == QuizAnswers.option_id).\
                where(QuizAnswers.option_id == answer_id, attempt_id == attempt_id)

            result = await session.execute(query)

            await session.commit()

            return result.scalars().first()

    @classmethod
    async def get_last_attempt(cls, tg_id: int, quiz_id: int) -> QuizAttempts:
        """Получение последней актуальной попытки прохождения квиза"""

        async with async_session() as session:
            query = select(QuizAttempts).\
                join(Users, Users.id == QuizAttempts.user_id).\
                where(Users.external_id == tg_id, QuizAttempts.quiz_id == quiz_id).\
                order_by(desc(QuizAttempts.id)).limit(1)

            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_quiz_attempts(cls, user: Users) -> list[QuizAttempts]:
        """Получение всех попыток прохождения квиза для данного пользователя"""

        status_complete = await cls.get_attempt_status('Завершен')
        async with async_session() as session:
            query = select(QuizAttempts).\
                where(
                QuizAttempts.user_id == user.id,
                QuizAttempts.status_id == status_complete.id
            ).order_by('created_at')
            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_answers_by_attempt(cls, attempt_id: int) -> list[QuizAnswers]:
        """Получение всех ответов для данной попытки прохождения квиза"""

        async with async_session() as session:
            query = select(
                QuizQuestions.title.label('question'),
                QuizQuestionOptions.title.label('answer'),
                QuizAnswers.created_at.label('created_at')
            ).\
                join(QuizAnswers, QuizQuestionOptions.id == QuizAnswers.option_id).\
                join(QuizQuestions, QuizQuestions.id == QuizQuestionOptions.question_id).\
                where(QuizAnswers.attempt_id == attempt_id)
            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def get_question_by_option(cls, option_id: str) -> str:
        """Получаем названия вопросов по id варианта ответа"""

        async with async_session() as session:

            q = select(
                QuizQuestions.title.label('question_title')).\
                join(QuizQuestionOptions, QuizQuestions.id == QuizQuestionOptions.question_id).\
                where(QuizQuestionOptions.id == option_id)

            res = await session.execute(q)

            return res.scalars().first()

    @classmethod
    async def get_quiz_id_by_name(cls, quiz_name: str):
        """Получение id квиза по его название"""

        async with async_session() as session:
            query = select(Quizes.id).where(Quizes.name.contains(quiz_name))
            res = await session.execute(query)

            return res.scalars().one_or_none()
