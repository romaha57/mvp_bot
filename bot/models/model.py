from sqlalchemy import Column, Integer, String, Text

from bot.db_connect import Base


class Settings(Base):
    __tablename__ = '$_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, comment='Название', index=True)
    text = Column(Text, nullable=False, comment='Текст от бота')
