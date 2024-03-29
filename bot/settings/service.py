import datetime

from sqlalchemy import select, update, text, insert

from bot.db_connect import async_session
from bot.services.base_service import BaseService
from bot.settings.model import Settings
from bot.users.models import Promocodes, PromocodeCourses, PromocodeQuizes, Users, Partners, UserAccount


class SettingsService(BaseService):
    @classmethod
    async def check_promocode(cls, promocode: str) -> Promocodes:
        """Проверяем существует ли промокод в БД"""

        async with async_session() as session:
            query = select(Promocodes).filter_by(code=promocode)
            result = await session.execute(query)

            return result.scalars().one_or_none()

    @classmethod
    async def add_promocode_partners(cls, promocode: Promocodes, user: UserAccount):

        async with async_session() as session:
            query = select(Partners).where(Partners.user_id == user.id)
            res = await session.execute(query)
            check_partners = res.scalars().first()

            if not check_partners:
                query = insert(Partners).values(sponsor_id=promocode.account_id, user_id=user.id)
                await session.execute(query)
                await session.commit()

    @classmethod
    async def increment_count_promocode(cls, promocode: Promocodes):
        """Увеличиваем счет активированных пользователей"""

        new_count = promocode.count_start + 1
        async with async_session() as session:
            query = update(Promocodes).where(Promocodes.id == promocode.id). \
                values(count_start=new_count)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def set_start_and_end_time_test_promo(cls, now: datetime.datetime, promocode: Promocodes, user: Users):
        end_time = now + datetime.timedelta(hours=promocode.duration)

        async with async_session() as session:
            query = update(Users).where(Users.id == user.id). \
                values(start_test_promo=now, end_test_promo=end_time)

            await session.execute(query)
            await session.commit()

