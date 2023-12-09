from typing import Union

from sqlalchemy import desc, insert, select, update

from bot.db_connect import async_session
from bot.lessons.models import (LessonAdditionalTaskHistory,
                                LessonAdditionalTaskHistoryStatuses,
                                LessonAdditionalTasks, LessonHistory,
                                LessonHistoryStatuses, Lessons,
                                LessonWorkTypes, TestLessonHistory,
                                TestLessonHistoryStatuses)
from bot.services.base_service import BaseService, Singleton
from bot.users.models import BonusRewards, BonusRewardsTypes, Users


class LessonService(BaseService, metaclass=Singleton):
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
            return result.mappings().all()

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
            get_lesson_history = select(LessonHistory).filter_by(
                lesson_id=lesson_id,
                user_id=user_id,
                course_history_id=course_history_id
            )
            res = await session.execute(get_lesson_history)
            lesson_history = res.scalars().first()

            if not lesson_history:
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
                order_by(desc('id')).limit(1)

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

            return result.scalars().all()

    @classmethod
    async def get_lesson_by_order_num(cls, course_id: int, order_num: int) -> Union[Lessons, None]:
        """Получаем урок по его курсу и порядковому номеру в этом курсе"""

        async with async_session() as session:
            query = select(Lessons).filter_by(course_id=course_id, order_num=order_num)
            result = await session.execute(query)

            return result.scalars().one_or_none()

    @classmethod
    async def get_type_task_for_lesson(cls, lesson: Lessons):
        """Получаем тип задания к данному уроку"""

        async with async_session() as session:
            query = select(LessonWorkTypes.id).\
                join(Lessons, LessonWorkTypes.id == Lessons.work_type_id).\
                where(Lessons.id == lesson.id)
            result = await session.execute(query)

            return result.scalars().one_or_none()

    @classmethod
    async def save_user_answer(cls, answer: str, lesson_history_id: int):
        """Сохраняем ответ пользователя на вопросы после урока"""

        async with async_session() as session:
            query = update(LessonHistory).\
                where(LessonHistory.id == lesson_history_id).\
                values(work_details=answer)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_additional_task_by_lesson(cls, lesson: Lessons):
        """Получаем доп задание для урока по его id"""

        async with async_session() as session:
            query = select(LessonAdditionalTasks).\
                join(Lessons, Lessons.additional_task_id == LessonAdditionalTasks.id).\
                where(Lessons.id == lesson.id)
            res = await session.execute(query)

            return res.scalars().first()

    @classmethod
    async def get_bonus_reward_type_by_name(cls, name: str):
        """Получение типа (начисление/списание) бонусов """

        async with async_session() as session:
            query = select(BonusRewardsTypes).where(BonusRewardsTypes.name == name)
            res = await session.execute(query)

            return res.scalars().first()

    @classmethod
    async def add_reward_to_user(cls, tg_id: int, reward: int, comment: str):
        """Добавляем награду пользователю"""

        account = await cls.get_account_by_tg_id(tg_id)
        type_add = await cls.get_bonus_reward_type_by_name('Начисление')

        async with async_session() as session:
            query = insert(BonusRewards).values(
                account_id=account.id,
                type_id=type_add.id,
                amount=reward,
                comment=comment

            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_lesson_additional_task_history_status_by_name(cls, name: str):
        """Получение статуса прохождения доп задания к уроку"""

        async with async_session() as session:
            query = select(LessonAdditionalTaskHistoryStatuses).\
                where(LessonAdditionalTaskHistoryStatuses.name == name)
            res = await session.execute(query)

            return res.scalars().first()

    @classmethod
    async def mark_additional_task_missed_status(cls, additional_task_history_id: int):
        """Отмечаем в истории прохождении доп задания статус 'Пропущен' """

        status = await cls.get_lesson_additional_task_history_status_by_name('Пропущен')

        async with async_session() as session:
            query = update(LessonAdditionalTaskHistory).\
                values(LessonAdditionalTaskHistory.status_id == status.id).\
                where(LessonAdditionalTaskHistory.id == additional_task_history_id)
            res = await session.execute(query)

            return res.scalars().first()

    @classmethod
    async def create_additional_task_history(cls, tg_id: int, additional_task_id: int, lesson_history_id: int):
        """Создаем запись о начале прохождения доп задания к уроку (по умолчанию статус пропущен)"""

        status = await cls.get_lesson_additional_task_history_status_by_name('Пропущен')
        user = await cls.get_user_by_tg_id(tg_id)

        async with async_session() as session:
            query = insert(LessonAdditionalTaskHistory).values(
                user_id=user.id,
                additional_task_id=additional_task_id,
                lesson_history_id=lesson_history_id,
                status_id=status.id
            )
            await session.execute(query)
            await session.commit()

            # получаем созданную историю прохождения доп задания
            query = select(LessonAdditionalTaskHistory).\
                filter_by(
                    user_id=user.id, additional_task_id=additional_task_id, lesson_history_id=lesson_history_id
            )
            additional_task_history = await session.execute(query)

            return additional_task_history.scalars().first()

    @classmethod
    async def mark_additional_task_done_status(cls, additional_task_history_id: int):
        """Отмечаем статус прохождеия доп задания к уроку на 'Сделан' """

        status = await cls.get_lesson_additional_task_history_status_by_name('Сделан')

        async with async_session() as session:
            query = update(LessonAdditionalTaskHistory).\
                where(LessonAdditionalTaskHistory.id == additional_task_history_id).\
                values(status_id=status.id)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def mark_additional_task_await_review_status(cls, additional_task_history_id: int):
        """Отмечаем статус прохождеия доп задания к уроку на 'Ожидает проверки' """

        status = await cls.get_lesson_additional_task_history_status_by_name('Ожидает проверки')

        async with async_session() as session:
            query = update(LessonAdditionalTaskHistory).\
                where(LessonAdditionalTaskHistory.id == additional_task_history_id).\
                values(status_id=status.id)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_users_in_awaited_status(cls):
        """Получаем tg_id пользователей, у которых статус прохождения доп задания 'Ожидает проверки' """

        status = await cls.get_lesson_additional_task_history_status_by_name('Ожидает проверки')

        async with async_session() as session:
            query = select(Users.external_id, LessonAdditionalTaskHistory.created_at, LessonAdditionalTaskHistory.id, LessonAdditionalTasks.reward, LessonAdditionalTasks.title).\
                join(LessonAdditionalTaskHistory, Users.id == LessonAdditionalTaskHistory.user_id).\
                join(LessonAdditionalTasks, LessonAdditionalTasks.id == LessonAdditionalTaskHistory.additional_task_id).\
                where(LessonAdditionalTaskHistory.status_id == status.id)

            res = await session.execute(query)
            return res.mappings().all()
