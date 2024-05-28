import datetime

from sqlalchemy import func, insert, select, update
from sqlalchemy.sql.functions import count

from bot.courses.service import CourseService
from bot.db_connect import async_session
from bot.lessons.models import Lessons
from bot.lessons.service import LessonService
from bot.quiz.service import QuizService
from bot.services.base_service import BaseService, Singleton
from bot.users.models import (BonusRewards, Promocodes, PromocodeTypes, UserAccount, Users, Partners, AnketaQuestions, AnketaAnswers, Reports)


class UserService(BaseService, metaclass=Singleton):

    @classmethod
    async def get_users_by_tg_id(cls, tg_id: int):
        """Получаем всех пользователей из таблицы $_users по их telegram_id"""

        async with async_session() as session:
            query = select(Users).filter_by(external_id=tg_id)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_connected_users(cls, sponsor_id: str):

        async with async_session() as session:
            query = select(count(Partners.id)).where(Partners.sponsor_id == sponsor_id, Partners.user_id != sponsor_id)
            result = await session.execute(query)

            return result.scalars().first()

    @classmethod
    async def get_promocode_by_tg_id(cls, tg_id: int) -> Promocodes:
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
                                 first_name: str = None, last_name: str = None):
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
    async def get_promocode_by_code(cls, code: str):
        async with async_session() as session:
            query = select(Promocodes).where(Promocodes.code == code)
            res = await session.execute(query)

            return res.scalars().first()

    @classmethod
    async def create_promocode(cls, name: str, code: str, account_id: int):
        """Создаем промокод"""

        promocode = await cls.get_promocode_by_code(code)
        if not promocode:
            async with async_session() as session:
                query = insert(Promocodes).values(
                    bot_id=1,
                    name=name,
                    code=code,
                    is_test=True,
                    account_id=account_id,
                    end_at=datetime.datetime.now() + datetime.timedelta(days=3000)
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


    @classmethod
    async def save_fullname(cls, fullname: str, tg_id: int):
        """Сохраняем ФИО для пользователя"""

        async with async_session() as session:
            query = update(Users).where(Users.external_id == tg_id).values(fullname=fullname)

            await session.execute(query)
            await session.commit()

    @classmethod
    async def get_fullname_by_tg_id(cls, tg_id: int):
        """Получение fullname пользователя для сертификата по tg_id"""

        async with async_session() as session:
            query = select(Users.fullname).where(Users.external_id == tg_id)
            res = await session.execute(query)

            return res.scalars().first()

    @classmethod
    async def get_unanswered_questions(cls, account_id: int):

        async with async_session() as session:
            all_anketa_questions_query = select(AnketaQuestions.id, AnketaQuestions.title, AnketaQuestions.order_num)

            res = await session.execute(all_anketa_questions_query)
            all_anketa_question = res.mappings().all()

            answered_questions_query = select(AnketaQuestions.id, AnketaQuestions.title, AnketaQuestions.order_num).\
                join(AnketaAnswers, AnketaAnswers.question_id == AnketaQuestions.id). \
                where(AnketaAnswers.account_id == account_id)

            res = await session.execute(answered_questions_query)
            answered_questions = res.mappings().all()

            unanswered_questions = list(set(all_anketa_question).difference(set(answered_questions)))
            unanswered_questions.sort(key=lambda elem: elem.get('order_num'))

            return unanswered_questions

    @classmethod
    async def save_user_report(cls, tg_id: int, text: str):

        async with async_session() as session:
            query = insert(Reports).values(
                tg_id=tg_id,
                text=text
            )

            await session.execute(query)
            await session.commit()

    @classmethod
    async def accept_politics(cls, tg_id: int):

        async with async_session() as session:
            query = update(Users).where(Users.external_id == tg_id).values(
                accept_politics=True
            )

            await session.execute(query)
            await session.commit()
