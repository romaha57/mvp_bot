from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Text,
                        func)
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
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    account = relationship('UserAccount', back_populates='user')

    quiz_attempts = relationship('QuizAttempts', back_populates='user')
    lesson_history = relationship('LessonHistory', back_populates='user')
    course_history = relationship('CourseHistory', back_populates='user')
    bot = relationship('Bots', back_populates='user')
    test_lesson_history = relationship('TestLessonHistory', back_populates='user')
    promocode = relationship('Promocodes', back_populates='user')

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

    code = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    bot = relationship('Bots', back_populates='promocode')
    course = relationship('Course', back_populates='promocode')
    quiz = relationship('Quizes', back_populates='promocode')
    user = relationship('Users', back_populates='promocode')

    def __str__(self):
        return f'{self.code}'
