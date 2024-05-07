from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Text, func)
from sqlalchemy.orm import relationship

from bot.db_connect import Base


class Users(Base):
    __tablename__ = '$_users'
    __tableargs__ = {
        'comment': 'Пользователи'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('$_user_accounts.id'))
    bot_id = Column(Integer, ForeignKey('$_bots.id'))
    promocode_id = Column(Integer, ForeignKey('$_promocodes.id'))
    start_test_promo = Column(DateTime)
    end_test_promo = Column(DateTime)
    external_id = Column(String)
    last_action = Column(DateTime)
    locked = Column(Text)
    state = Column(String)
    tags = Column(String)
    username = Column(String)
    fullname = Column(String)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    account = relationship('UserAccount', back_populates='user')

    quiz_attempts = relationship('QuizAttempts', back_populates='user')
    lesson_history = relationship('LessonHistory', back_populates='user')
    course_history = relationship('CourseHistory', back_populates='user')
    bot = relationship('Bots', back_populates='user')
    test_lesson_history = relationship('TestLessonHistory', back_populates='user')
    promocode = relationship('Promocodes', back_populates='user')
    lesson_additional_history_task = relationship('LessonAdditionalTaskHistory', back_populates='user')
    rating = relationship('RatingLesson', back_populates='user')

    def __str__(self):
        return f'{self.username} - {self.external_id}'


class UserAccount(Base):
    __tablename__ = '$_user_accounts'
    __tableargs__ = {
        'comment': 'Аккаунты(уникальные)'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship('Users', back_populates='account')
    bonus_reward = relationship('BonusRewards', back_populates='account')
    promocode = relationship('Promocodes', back_populates='account')


    def __str__(self):
        return f'{self.first_name} - {self.last_name} - {self.phone}'


class Promocodes(Base):
    __tablename__ = '$_promocodes'
    __tableargs__ = {
        'comment': 'Промокоды'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('$_bots.id'))
    type_id = Column(Integer, ForeignKey('$_promocode_types.id'))
    account_id = Column(Integer, ForeignKey('$_user_accounts.id'))
    name = Column(String)
    code = Column(String, nullable=False)
    actual = Column(Integer, default=1)
    count_start = Column(Integer)
    is_test = Column(Boolean, default=False)
    lesson_cnt = Column(Integer)
    duration = Column(Integer)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    bot = relationship('Bots', back_populates='promocode')
    user = relationship('Users', back_populates='promocode')
    account = relationship('UserAccount', back_populates='promocode')
    type = relationship('PromocodeTypes', back_populates='promocode')
    promocodes_courses = relationship('PromocodeCourses', back_populates='promocode')
    promocodes_quizes = relationship('PromocodeQuizes', back_populates='promocode')

    def __str__(self):
        return f'{self.code}'


class PromocodeTypes(Base):
    __tablename__ = '$_promocode_types'
    __tableargs__ = {
        'comment': 'Роли для промокодов'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    promocode = relationship('Promocodes', back_populates='type')

    def __str__(self):
        return f'{self.name}'


class BonusRewards(Base):
    __tablename__ = '$_bonus_rewards'
    __tableargs__ = {
        'comment': 'Зачисления бонусов'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('$_user_accounts.id'))
    type_id = Column(Integer, ForeignKey('$_bonus_reward_types.id'))
    amount = Column(Integer)
    comment = Column(Text)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    account = relationship('UserAccount', back_populates='bonus_reward')
    type = relationship('BonusRewardsTypes', back_populates='bonus_reward')

    def __str__(self):
        return f'{self.amount}'


class BonusRewardsTypes(Base):
    __tablename__ = '$_bonus_reward_types'
    __tableargs__ = {
        'comment': 'Типы зачисления бонусов'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    bonus_reward = relationship('BonusRewards', back_populates='type')

    def __str__(self):
        return f'{self.name}'


class RatingLesson(Base):
    __tablename__ = '$_rating_lesson'
    __tableargs__ = {
        'comment': 'Оценки пользователей к уроку'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey('$_lessons.id'))
    user_id = Column(Integer, ForeignKey('$_users.id'))
    rating = Column(Text)

    lesson = relationship('Lessons', back_populates='rating')
    user = relationship('Users', back_populates='rating')

    def __str__(self):
        return f'{self.rating}'


class PromocodeCourses(Base):
    __tablename__ = '$_promocodes_courses'
    __tableargs__ = {
        'comment': 'Курсы привязанные к промокоду'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    promocode_id = Column(Integer, ForeignKey('$_promocodes.id'))
    course_id = Column(Integer, ForeignKey('$_courses.id'))

    promocode = relationship('Promocodes', back_populates='promocodes_courses')
    course = relationship('Course', back_populates='promocodes_courses')

    def __str__(self):
        return f'promocode_id:{self.promocode_id} - course_id:{self.course_id}'


class PromocodeQuizes(Base):
    __tablename__ = '$_promocodes_quizes'
    __tableargs__ = {
        'comment': 'Квизы привязанные к промокоду'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    promocode_id = Column(Integer, ForeignKey('$_promocodes.id'))
    quiz_id = Column(Integer, ForeignKey('$_quizes.id'))

    promocode = relationship('Promocodes', back_populates='promocodes_quizes')
    quiz = relationship('Quizes', back_populates='promocodes_quizes')

    def __str__(self):
        return f'promocode_id:{self.promocode_id} - quiz_id:{self.quiz_id}'


class Partners(Base):
    __tablename__ = '$_partners'
    __table_args__ = {
        'comment': 'Реферальная программа'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('$_user_accounts.id'))
    sponsor_id = Column(Integer, ForeignKey('$_user_accounts.id'))

    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    def __str__(self):
        return f'user_id:{self.user_id} - sponsor_id:{self.sponsor_id}'


class AnketaQuestions(Base):
    __tablename__ = '$_anketa_questions'
    __table_args__ = {
        'comment': 'Вопросы для анкет пользователей'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text)
    order_num = Column(Integer)

    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    def __str__(self):
        return f'{self.title} - {self.order_num}'


class AnketaAnswers(Base):
    __tablename__ = '$_anketa_answers'
    __table_args__ = {
        'comment': 'Ответы для анкет пользователей'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey('$_anketa_questions.id'))
    account_id = Column(Integer, ForeignKey('$_user_accounts.id'))
    answer = Column(Text)

    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    def __str__(self):
        return f'{self.question_id} - {self.account_id}'


class Reports(Base):
    __tablename__ = '$_reports'
    __table_args__ = {
        'comment': 'Ошибки пользователей'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(String)
    text = Column(Text)

    created_at = Column(DateTime, server_default=func.now())

    def __str__(self):
        return f'{self.tg_id} - {self.text}'


class AttachmentsTypes(Base):
    __tablename__ = '$_attachment_types'
    __table_args__ = {
        'comment': 'Файл загрузки контента'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    def __str__(self):
        return f'{self.name}'


class Attachments(Base):
    __tablename__ = '$_attachments'
    __table_args__ = {
        'comment': 'Файл загрузки контента'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('$_bots.id'))
    file_id = Column(String)
    filename = Column(String)
    type_id = Column(Integer, ForeignKey('$_attachment_types.id'))
    extension = Column(String)
    label = Column(String)

    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    def __str__(self):
        return f'{self.file_id}'
