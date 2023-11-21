from sqlalchemy import insert, select, func

from bot.db_connect import async_session
from bot.lessons.service import LessonService
from bot.services.base_service import BaseService
from bot.users.models import UserAccount, Users, BonusRewards, BonusRewardsTypes


class UserService(BaseService):

    @classmethod
    async def get_users_by_tg_id(cls, tg_id: int):
        """Получаем всех пользователей из таблицы $_users по их telegram_id"""

        async with async_session() as session:
            query = select(Users).filter_by(external_id=tg_id)
            result = await session.execute(query)

            return result.mappings().all()

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
