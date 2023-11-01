from sqlalchemy import select, insert, CursorResult, desc, update, func, distinct

from bot.db_connect import async_session
from bot.services.base_service import BaseService

from bot.lessons.models import Lessons, LessonHistory, LessonHistoryStatuses, TestLessonHistory, \
    TestLessonHistoryStatuses


class LessonService(BaseService):
    model = None

    @classmethod
    async def get_lessons(cls, course_id: str):
        async with async_session() as session:
            query = select(Lessons.title).where(Lessons.course_id == course_id).order_by('order_num')

            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_lesson_by_name(cls, name: str):
        print('name', name)
        async with async_session() as session:
            query = select(Lessons).filter_by(title=name)
            result = await session.execute(query)

            return result.scalars().one_or_none()

    @classmethod
    async def get_lesson_history_status(cls, name):
        """Получаем статус для истории прохождении урока"""

        async with async_session() as session:
            query = select(LessonHistoryStatuses).filter_by(name=name)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_test_lesson_history_status(cls, name):
        """Получаем статус для тестовых вопросов в истории прохождении урока"""

        async with async_session() as session:
            query = select(TestLessonHistoryStatuses).filter_by(name=name)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def create_history(cls, lesson_id: int, user_id: int, course_history_id: int):
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
    async def get_actual_lesson_history(cls, user_id: int, lesson_id: int):
        """Получаем актуальную попытку прохождения урока"""

        async with async_session() as session:
            query = select(LessonHistory).filter_by(user_id=user_id, lesson_id=lesson_id).order_by(desc('id'))
            result = await session.execute(query)

            return result.scalars().first()    \

    @classmethod
    async def get_actual_test_lesson_history(cls, user_id: int, lesson_id: int):
        """Получаем актуальную попытку прохождения теста после урока"""

        async with async_session() as session:
            query = select(TestLessonHistory).filter_by(user_id=user_id, lesson_id=lesson_id).order_by(desc('id'))
            result = await session.execute(query)

            return result.scalars().first()


    @classmethod
    async def create_test_history(cls, user_id: int, lesson_id: int, lesson_history_id: int):
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
    async def mark_lesson_history_on_status_test(cls, lesson_history_id):
        """Отмечаем статус прохождеия урока на 'ТЕСТ' """

        status = await cls.get_lesson_history_status('Тест')
        async with async_session() as session:
            query = update(LessonHistory).where(LessonHistory.id == lesson_history_id).values(status_id=status.id)
            await session.execute(query)
            await session.commit()    \

    @classmethod
    async def mark_lesson_history_on_status_done(cls, lesson_history_id):
        """Отмечаем статус прохождеия урока на 'Пройден' """

        status = await cls.get_test_lesson_history_status('Пройден')
        async with async_session() as session:
            query = update(TestLessonHistory).where(TestLessonHistory.lesson_history_id == lesson_history_id).values(status_id=status.id)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def save_test_answers(cls, answers: list[str], lesson_history_id: int ):
        """Сохраняем ответы пользователя на тест после урока"""

        answers = str(answers)
        async with async_session() as session:
            query = update(TestLessonHistory).where(TestLessonHistory.lesson_history_id==lesson_history_id).\
                values(answers=answers)
            await session.execute(query)
            await session.commit()
