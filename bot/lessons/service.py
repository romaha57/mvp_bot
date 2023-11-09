from typing import Union

from sqlalchemy import desc, insert, select, update

from bot.db_connect import async_session
from bot.lessons.models import (LessonHistory, LessonHistoryStatuses, Lessons,
                                TestLessonHistory, TestLessonHistoryStatuses)
from bot.services.base_service import BaseService
from bot.users.models import Users


class LessonService(BaseService):
    model = None

    @classmethod
    async def get_lessons(cls, course_id: str) -> list[dict]:
        """Получение всех уроков для данного курса"""

        async with async_session() as session:
            query = select(Lessons.title, LessonHistory.status_id, LessonHistory.user_id, Lessons.order_num).\
                join(LessonHistory, LessonHistory.lesson_id == Lessons.id, isouter=True).\
                join(Users, Users.id == LessonHistory.user_id, isouter=True). \
                where(Lessons.course_id == course_id).\
                order_by('order_num')

            result = await session.execute(query)
            return result.unique().mappings().all()

    @classmethod
    async def get_lesson_by_name(cls, name: str) -> Union[Lessons, None]:
        """Получение урока по его названию"""

        async with async_session() as session:
            query = select(Lessons).filter(Lessons.title.contains(name))
            result = await session.execute(query)
            return result.scalars().first()

    @classmethod
    async def get_lesson_history_status(cls, name: str) -> LessonHistoryStatuses:
        """Получаем статус для истории прохождения урока"""

        async with async_session() as session:
            query = select(LessonHistoryStatuses).filter_by(name=name)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_test_lesson_history_status(cls, name: str) -> TestLessonHistoryStatuses:
        """Получаем статус для тестовых вопросов в истории прохождении урока"""

        async with async_session() as session:
            query = select(TestLessonHistoryStatuses).filter_by(name=name)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def create_history(cls, lesson_id: int, user_id: int, course_history_id: int):
        """Создание истории прохождения урока"""

        status = await cls.get_lesson_history_status('Видео')

        async with async_session() as session:
            query = insert(LessonHistory).values(
                lesson_id=lesson_id,
                user_id=user_id,
                status_id=status.id,
                course_history_id=course_history_id
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_actual_lesson_history(cls, user_id: int, lesson_id: int) -> LessonHistory:
        """Получаем актуальную попытку прохождения урока"""

        async with async_session() as session:
            query = select(LessonHistory).\
                filter_by(user_id=user_id, lesson_id=lesson_id).\
                order_by(desc('id'))

            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_actual_test_lesson_history(cls, user_id: int, lesson_id: int) -> TestLessonHistory:
        """Получаем актуальную попытку прохождения теста после урока"""

        async with async_session() as session:
            query = select(TestLessonHistory).\
                filter_by(user_id=user_id, lesson_id=lesson_id).\
                order_by(desc('id'))

            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def create_test_history(cls, user_id: int, lesson_id: int, lesson_history_id: int):
        """Создание истории прохождения тестирования после урока"""

        status = await cls.get_test_lesson_history_status('В процессе')

        async with async_session() as session:
            query = insert(TestLessonHistory).values(
                lesson_id=lesson_id,
                user_id=user_id,
                status_id=status.id,
                lesson_history_id=lesson_history_id
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def mark_lesson_history_on_status_test(cls, lesson_history_id: int):
        """Отмечаем статус прохождеия урока на 'ТЕСТ' """

        status = await cls.get_lesson_history_status('Тест')
        async with async_session() as session:
            query = update(LessonHistory).\
                where(LessonHistory.id == lesson_history_id).\
                values(status_id=status.id)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def mark_lesson_history_on_status_complete(cls, lesson_history_id: int):
        """Отмечаем статус прохождеия урока на 'Пройден' """

        status = await cls.get_lesson_history_status('Пройден')
        async with async_session() as session:
            query = update(LessonHistory).\
                where(LessonHistory.id == lesson_history_id).\
                values(status_id=status.id)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def mark_lesson_history_on_status_fail_test(cls, lesson_history_id: int):
        """Отмечаем статус прохождения урока на 'Завален тест' """

        status = await cls.get_lesson_history_status('Завален тест')
        async with async_session() as session:
            query = update(LessonHistory).\
                where(LessonHistory.id == lesson_history_id).\
                values(status_id=status.id)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def mark_lesson_history_on_status_done(cls, lesson_history_id: int):
        """Отмечаем статус прохождения урока на 'Пройден' """

        status = await cls.get_lesson_history_status('Пройден')

        async with async_session() as session:
            query = update(LessonHistory).\
                where(LessonHistory.id == lesson_history_id).\
                values(status_id=status.id)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def save_test_answers(cls, answers: list[str], lesson_history_id: int):
        """Сохраняем ответы пользователя на тест после урока"""

        answers = str(answers)
        async with async_session() as session:
            query = update(TestLessonHistory).\
                where(TestLessonHistory.lesson_history_id == lesson_history_id).\
                values(answers=answers)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_correct_answer_by_lesson(cls, lesson_id: int) -> list[str]:
        """Получаем правильные ответы на тесты к уроку"""

        async with async_session() as session:
            query = select(Lessons.questions).filter_by(id=lesson_id)
            result = await session.execute(query)
            await session.commit()

            return result.unique().scalars().all()

    @classmethod
    async def get_lesson_by_order_num(cls, course_id: int, order_num: int) -> Union[Lessons, None]:
        """Получаем урок по его курсу и порядковому номеру в этом курсе"""

        async with async_session() as session:
            query = select(Lessons).filter_by(course_id=course_id, order_num=order_num)
            result = await session.execute(query)

            return result.unique().scalars().one_or_none()
