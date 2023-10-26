from sqlalchemy import Column, Integer, String

from bot.db_connect import Base


class Test(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)


