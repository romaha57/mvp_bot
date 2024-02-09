from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from sqlalchemy.testing.schema import Column

from bot.db_connect import Base


class KnowledgeBase(Base):
    __tablename__ = '$_knowledge_base'
    __tableargs__ = {
        'comment': 'Документы базы знаний '
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    divide_id = Column(Integer, ForeignKey('$_knowledge_base_divides'))
    type_id = Column(Integer, ForeignKey('$_knowledge_base_types'))
    document = Column(String)
    available = Column(Integer)
    order_num = Column(Integer)
    keywords = Column(String)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    divide = relationship('KnowledgeBaseDivides', back_populates='knowledge_base')
    type = relationship('KnowledgeBaseTypes', back_populates='knowledge_base')

    def __str__(self):
        return f'{self.title}'


class KnowledgeBaseDivides(Base):
    __tablename__ = '$_knowledge_base_divides'
    __tableargs__ = {
        'comment': 'Папки для базы знаний'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey('$_knowledge_base_divides'))
    order_num = Column(Integer)
    keywords = Column(String)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    knowledge_base = relationship('KnowledgeBase', back_populates='divide')
    parent = relationship('KnowledgeBaseDivides', back_populates='divide')

    def __str__(self):
        return f'{self.title}'


class KnowledgeBaseTypes(Base):
    __tablename__ = '$_knowledge_base_types'
    __tableargs__ = {
        'comment': 'Тип документа базы знаний'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    knowledge_base = relationship('KnowledgeBase', back_populates='type')

    def __str__(self):
        return f'{self.name}'
