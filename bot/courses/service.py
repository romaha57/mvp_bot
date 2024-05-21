from typing import Union

from sqlalchemy import desc, insert, or_, select, update

from bot.courses.models import (Course, CourseBots, CourseHistory,
                                CourseHistoryStatuses)
from bot.db_connect import async_session
from bot.lessons.models import LessonHistory
from bot.services.base_service import BaseService, Singleton
from bot.users.models import Users, PromocodeQuizes, PromocodeCourses


class CourseService(BaseService, metaclass=Singleton):

    @classmethod
    async def get_all_courses(cls):
        async with async_session() as session:
            query = select(Course.id, Course.title, Course.order_num).where(Course.is_public == True)
            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def get_courses_by_bot(cls, tg_id: int):
        async with async_session() as session:
            query = select(Course.id, Course.title, Course.order_num).\
                join(CourseBots, Course.id == CourseBots.course_id).\
                join(Users, Users.bot_id == CourseBots.bot_id).\
                where(Users.external_id == tg_id, Course.is_public == True)
            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def get_courses_by_promo(cls, tg_id: int):
        async with async_session() as session:
            query = select(Course.id, Course.title, Course.order_num).\
                join(PromocodeCourses, PromocodeCourses.course_id== Course.id).\
                join(Users, Users.promocode_id == PromocodeCourses.promocode_id).\
                where(Users.external_id == tg_id, Course.is_public == True)
            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def get_course_by_last_course_history(cls, tg_id: int):
        async with async_session() as session:
            query = select(Course.id).\
                join(CourseHistory, CourseHistory.course_id == Course.id).\
                join(Users, CourseHistory.user_id == Users.id).\
                where(Users.external_id == tg_id).order_by(desc(CourseHistory.id)).limit(1)

            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_course_by_name(cls, course_name: str) -> Union[Course, None]:
        """Получаем курс по его названию"""

        async with async_session() as session:
            query = select(Course).filter_by(title=course_name)
            result = await session.execute(query)

            return result.scalars().one_or_none()

    @classmethod
    async def get_course_by_id(cls, course_id: str) -> Union[Course, None]:
        """Получаем курс по его id"""

        async with async_session() as session:
            query = select(Course).filter_by(id=course_id)
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
    async def get_or_create_history(cls, course_id: int, user: Users):
        """Создание истории прохождения курса"""

        status = await cls.get_course_history_status('Открыт')
        async with async_session() as session:
            get_history = select(CourseHistory).filter_by(
                course_id=course_id,
                user_id=user.id
            )
            res = await session.execute(get_history)
            history = res.scalars().first()

            if not history:

                query = insert(CourseHistory).values(
                    course_id=course_id,
                    user_id=user.id,
                    status_id=status.id,
                    is_show_description=True
                )
                await session.execute(query)
                await session.commit()

                get_history = select(CourseHistory).filter_by(
                    course_id=course_id,
                    user_id=user.id
                )
                res = await session.execute(get_history)
                history = res.scalars().first()

            return history

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

    @classmethod
    async def get_course_history_id_by_lesson_history(cls, lesson_history_id: int):
        """Получаем id прохожения курса по истории прохождения урока"""

        async with async_session() as session:
            query = select(CourseHistory.id).\
                join(LessonHistory, LessonHistory.course_history_id == CourseHistory.id). \
                where(LessonHistory.id == lesson_history_id)
            res = await session.execute(query)

            return res.scalars().first()    \


    @classmethod
    async def get_course_by_course_history_id(cls, course_history_id: int):
        """Получаем курс по истории прохождения урока"""

        async with async_session() as session:
            query = select(Course).\
                join(CourseHistory, CourseHistory.course_id == Course.id). \
                where(CourseHistory.id == course_history_id)
            res = await session.execute(query)

            return res.scalars().first()

    @classmethod
    async def mark_course_done(cls, course_history_id: int):
        """Отмечаем курс как пройденный"""

        status = await cls.get_course_history_status('Пройден')
        async with async_session() as session:
            query = update(CourseHistory). \
                where(CourseHistory.id == course_history_id). \
                values(status_id=status.id)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def mark_show_course_description(cls, course_history: CourseHistory, flag: bool):
        """Отмечаем флаг у значения для показа стартового видео курса"""

        async with async_session() as session:
            query = update(CourseHistory). \
                where(CourseHistory.id == course_history.id). \
                values(is_show_description=flag)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_actual_lesson_history(cls, user_id: int, lesson_id: int) -> LessonHistory:
        """Получаем актуальную попытку прохождения урока"""

        async with async_session() as session:
            query = select(LessonHistory). \
                filter_by(user_id=user_id, lesson_id=lesson_id). \
                order_by(desc('id')).limit(1)

            result = await session.execute(query)

            return result.scalars().first()
