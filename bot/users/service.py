from sqlalchemy import func, insert, select

from bot.courses.service import CourseService
from bot.db_connect import async_session
from bot.lessons.service import LessonService
from bot.quiz.service import QuizService
from bot.services.base_service import BaseService, Singleton
from bot.users.models import (BonusRewards, Promocodes, PromocodeTypes,
                              UserAccount, Users)


class UserService(BaseService, metaclass=Singleton):

    @classmethod
    async def get_users_by_tg_id(cls, tg_id: int):
        """Получаем всех пользователей из таблицы $_users по их telegram_id"""

        async with async_session() as session:
            query = select(Users).filter_by(external_id=tg_id)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_promocode_by_tg_id(cls, tg_id: int):
        """Получаем промокод по tg_id"""

        async with async_session() as session:
            query = select(Promocodes).\
                join(Users, Users.promocode_id == Promocodes.id).\
                where(Users.external_id == tg_id)

            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_or_create_account(cls, first_name: str, last_name: str):
        """Создание или получение аккаунта пользователя(аккаунт=человек)"""

        async with async_session() as session:

            query = select(UserAccount).filter_by(first_name=first_name, last_name=last_name)
            result = await session.execute(query)
            await session.commit()

            account = result.scalars().first()

            if not account:
                query = insert(UserAccount).values(
                    first_name=first_name,
                    last_name=last_name
                )
                await session.execute(query)
                await session.commit()

                query = select(UserAccount).filter_by(
                    first_name=first_name,
                    last_name=last_name
                )
                res = await session.execute(query)
                account = res.scalars().first()

            return account

    @classmethod
    async def get_or_create_user(cls, username: str, tg_id: int, bot_id: int = None,
                                 promocode_id: int = None, first_name: str = None, last_name: str = None):
        """Создание или получение пользователя из БД"""

        user = await cls.get_users_by_tg_id(
            tg_id=tg_id
        )
        if not user:
            account = await cls.get_or_create_account(
                first_name=first_name,
                last_name=last_name
            )

            async with async_session() as session:
                query = insert(Users).values(
                    username=username,
                    bot_id=bot_id,
                    external_id=tg_id,
                    promocode_id=promocode_id,
                    account_id=account.id
                )
                await session.execute(query)
                await session.commit()

    @classmethod
    async def get_balance(cls, account_id: int) -> int:
        """Получаем баланс для текущего аккаунта (из всех начислений вычитаем все списания)"""

        status_accrual = await LessonService.get_bonus_reward_type_by_name('Начисление')
        status_debited = await LessonService.get_bonus_reward_type_by_name('Списание')

        async with async_session() as session:
            # получаем сумму всех начислений
            query = select(func.sum(BonusRewards.amount)).\
                where(BonusRewards.type_id == status_accrual.id, BonusRewards.account_id == account_id)
            res = await session.execute(query)

            sum_accrual = res.scalars().first()

            # получаем сумму всех списаний со счета
            query = select(func.sum(BonusRewards.amount)).\
                where(BonusRewards.type_id == status_debited.id, BonusRewards.account_id == account_id)
            res = await session.execute(query)

            sum_debited = res.scalars().first()
            if not sum_debited:
                sum_debited = 0

        return sum_accrual - sum_debited

    @classmethod
    async def get_promocode_roles(cls):
        """Получение всех ролей для промокода"""

        async with async_session() as session:
            query = select(PromocodeTypes.name)
            res = await session.execute(query)

            return res.scalars().all()

    @classmethod
    async def get_promocode_role_id_by_name(cls, role: str):
        """Получение роли для промокода"""

        async with async_session() as session:
            query = select(PromocodeTypes.id).where(PromocodeTypes.name == role)
            res = await session.execute(query)

            return res.scalars().one_or_none()

    @classmethod
    async def create_promocode(cls, course_name: str, quiz_name: str, role: str, code: str, account_id: int):
        """Создаем промокод"""

        course_id = await CourseService.get_course_id_by_name(course_name)

        quiz_id = await QuizService.get_quiz_id_by_name(quiz_name)
        role_id = await UserService.get_promocode_role_id_by_name(role)

        async with async_session() as session:
            query = insert(Promocodes).values(
                bot_id=1,
                course_id=course_id,
                quiz_id=quiz_id,
                type_id=role_id,
                code=code,
                account_id=account_id
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_created_promocodes_by_manager(cls, account_id: int):
        """Получение всех промокодов, сгенерированных данным пользователем"""

        async with async_session() as session:
            query = select(Promocodes).where(Promocodes.account_id == account_id)

            res = await session.execute(query)
            return res.scalars().all()

    @classmethod
    async def get_users_by_id(cls, users_ids: list[int]):
        """Получаем всех юзеров из БД по списку их id"""

        async with async_session() as session:
            query = select(Users).where(Users.id.in_(users_ids))
            res = await session.execute(query)

            return res.scalars().all()
