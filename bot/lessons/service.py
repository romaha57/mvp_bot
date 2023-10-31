from sqlalchemy import select

from bot.db_connect import async_session
from bot.services.base_service import BaseService

from bot.lessons.models import Lessons


class LessonService(BaseService):
    model = None

    @classmethod
    async def get_lessons(cls, course_id: int):
        async with async_session() as session:
            query = select(Lessons).filter_by(course_id=course_id)
            result = await session.execute(query)

            return result.scalars().all()
