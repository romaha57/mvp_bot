from sqlalchemy import select, update, insert

from bot.db_connect import async_session
from bot.services.base_service import BaseService

from bot.courses.models import Course, CourseHistory, CourseHistoryStatuses, CourseBots
from bot.users.service import UserService


class CourseService(BaseService):
    model = None

    @classmethod
    async def get_courses_ids_by_promo(cls, course_id: int):
        """Получаем все доступные id_курсов доступных по промокоду"""

        async with async_session() as session:
            query = select(Course.id).filter_by(id=course_id)
            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_courses_ids_by_bot(cls, bot_id: int):
        """Получаем все доступные id_курсов этого бота"""

        async with async_session() as session:
            query = select(Course.id).join(CourseBots, Course.id == CourseBots.course_id).where(CourseBots.bot_id==bot_id)
            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_courses(cls, courses_ids: set[int]):
        """Получаем все доступные курсы этого бота"""

        async with async_session() as session:
            query = select(Course).filter(Course.id.in_(courses_ids))
            result = await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def get_course_by_name(cls, course_name: str):
        """Получаем курс по его названию"""

        async with async_session() as session:
            query = select(Course).filter_by(title=course_name)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def create_history(cls, course_id: int, tg_id: int):
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
    async def get_course_history_status(cls, status_name: str):
        """Получаем статус истории курса по названию статуса"""

        async with async_session() as session:
            query = select(CourseHistoryStatuses).filter_by(name=status_name)
            result = await session.execute(query)

            return result.scalars().first()

