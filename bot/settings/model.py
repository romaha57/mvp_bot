from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy import func
from sqlalchemy.orm import relationship

from bot.db_connect import Base


class Settings(Base):
    __tablename__ = '$_settings'
    __tableargs__ = {
        'comment': 'Настройки бота'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, nullable=False)
    label = Column(Text)
    value = Column(Text, nullable=False)
    order_num = Column(Integer, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    type_id = Column(Integer, ForeignKey('$_setting_types.id'))
    type = relationship('SettingsTypes', back_populates='settings')

    def __str__(self):
        return f'{self.key}'


class SettingsTypes(Base):
    __tablename__ = '$_setting_types'
    __tableargs__ = {
        'comment': 'Тип настройки бота'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    settings = relationship('Settings', back_populates='type')

    def __str__(self):
        return f'{self.name}'
