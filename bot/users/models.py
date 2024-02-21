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
    course_id = Column(Integer, ForeignKey('$_courses.id'))
    quiz_id = Column(Integer, ForeignKey('$_quizes.id'))
    type_id = Column(Integer, ForeignKey('$_promocode_types.id'))
    account_id = Column(Integer, ForeignKey('$_user_accounts.id'))

    code = Column(String, nullable=False)
    actual = Column(Integer, default=1)
    count_start = Column(Integer)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    bot = relationship('Bots', back_populates='promocode')
    course = relationship('Course', back_populates='promocode')
    quiz = relationship('Quizes', back_populates='promocode')
    user = relationship('Users', back_populates='promocode')
    account = relationship('UserAccount', back_populates='promocode')
    type = relationship('PromocodeTypes', back_populates='promocode')

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
