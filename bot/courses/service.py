from typing import Union

from sqlalchemy import desc, insert, select, func, distinct, or_

from bot.courses.models import (Course, CourseBots, CourseHistory,
                                CourseHistoryStatuses)
from bot.db_connect import async_session
from bot.services.base_service import BaseService
from bot.users.models import Promocodes


class CourseService(BaseService):
    model = None


    @classmethod
    async def get_all_courses(cls):
        async with async_session() as session:
            query = select(Course.title)
            res = await session.execute(query)

            return res.scalars().all()

    @classmethod
    async def get_course_by_promo_and_bot(cls, promocode_course_id: int, bot_id: int):
        """Получение курсов доступныз для самого бота и для промокода"""
        async with async_session() as session:
            query = select(Course.title).\
                join(CourseBots, Course.id == CourseBots.course_id).\
                where(or_(Course.id == promocode_course_id, CourseBots.id == bot_id))
            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_course_by_name(cls, course_name: str) -> Union[Course, None]:
        """Получаем курс по его названию"""

        async with async_session() as session:
            query = select(Course).filter_by(title=course_name)
            result = await session.execute(query)

            return result.scalars().one_or_none()

    @classmethod
    async def get_course_id_by_name(cls, course_name: str) -> Union[Course, None]:
        """Получаем курс по его названию"""

        async with async_session() as session:
            query = select(Course.id).filter_by(title=course_name)
            result = await session.execute(query)

            return result.scalars().one_or_none()

    @classmethod
    async def create_history(cls, course_id: int, tg_id: int):
        """Создание истории прохождения курса"""

        user = await cls.get_user_by_tg_id(tg_id)
        status = await cls.get_course_history_status('Открыт')
        async with async_session() as session:
            query = insert(CourseHistory).values(
                course_id=course_id,
                user_id=user.id,
                status_id=status.id
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_course_history_status(cls, status_name: str) -> CourseHistoryStatuses:
        """Получаем статус истории курса по названию статуса"""

        async with async_session() as session:
            query = select(CourseHistoryStatuses).filter_by(name=status_name)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_actual_course_attempt(cls, user_id: int, course_id: int):
        """Получаем актуальную попытку прохождения курса"""

        async with async_session() as session:
            query = select(CourseHistory).\
                filter_by(user_id=user_id, course_id=course_id).\
                order_by(desc('id'))

            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_group_id(cls, course_id: int):
        """Получение id группы для отправки овтетов пользователя"""

        async with async_session() as session:
            query = select(Course.group_id).where(Course.id == course_id)

            res = await session.execute(query)

            return res.scalars().first()
