from sqlalchemy import (BigInteger, Column, DateTime, ForeignKey, Integer,
                        String, func)
from sqlalchemy.orm import relationship

from bot.db_connect import Base


class Bots(Base):
    __tablename__ = '$_bots'
    __tableargs__ = {
        'comment': 'Боты'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('$_clients.id'))
    external_id = Column(BigInteger, nullable=False)
    functionality_id = Column(Integer, ForeignKey('$_bot_functionalities.id'))
    messenger_id = Column(Integer, ForeignKey('$_bots_messengers.id'))
    name = Column(String, nullable=False)
    token = Column(String, nullable=False)
    username = Column(String, nullable=False)
    order_num = Column(Integer, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    client = relationship('Clients', back_populates='bot')
    functionality = relationship('BotsFunctionalities', back_populates='bot')
    messenger = relationship('BotsMessengers', back_populates='bot')

    bots_course = relationship('CourseBots', back_populates='bots_course')

    quiz_bots = relationship('QuizBots', back_populates='bot')
    promocode = relationship('Promocodes', back_populates='bot')
    user = relationship('Users', back_populates='bot')

    def __str__(self):
        return f'{self.name}'


class BotsMessengers(Base):
    __tablename__ = '$_bots_messengers'
    __tableargs__ = {
        'comment': 'Какому сервису принадлежит'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    bot = relationship('Bots', back_populates='messenger')

    def __str__(self):
        return f'{self.name}'


class BotsFunctionalities(Base):
    __tablename__ = '$_bot_functionalities'
    __tableargs__ = {
        'comment': 'Функционал бота'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    bot = relationship('Bots', back_populates='functionality')

    def __str__(self):
        return f'{self.name}'
