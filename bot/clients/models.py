from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from bot.db_connect import Base


class Clients(Base):
    __tablename__ = '$_clients'
    __tableargs__ = {
        'comment': 'Клиенты бота'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey('$_client_categories.id'))
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    category = relationship('ClientCategories', back_populates='client')
    bot = relationship('Bots', back_populates='client')

    def __str__(self):
        return f'{self.name}'


class ClientCategories(Base):
    __tablename__ = '$_client_categories'
    __tableargs__ = {
        'comment': 'Категории клиента'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    client = relationship('Clients', back_populates='category')

    def __str__(self):
        return f'{self.name}'
