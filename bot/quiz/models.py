from sqlalchemy import ForeignKey, func, Integer, Column, String, DateTime, Text
from sqlalchemy.orm import relationship

from bot.db_connect import Base


class Quizes(Base):
    __tablename__ = '$_quizes'
    __tableargs__ = {
        'comment': 'Квизы'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    cnt = Column(Integer)
    description = Column(Text)
    outro = Column(Text)
    type_id = Column(Integer, ForeignKey('$_quiz_types.id'))
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    type = relationship('QuizTypes', back_populates='quiz')
    quiz_questions = relationship('QuizQuestions', back_populates='quiz')
    quiz_bots = relationship('QuizBots', back_populates='quiz')
    quiz_attempts = relationship('QuizAttempts', back_populates='quiz')
    promocode = relationship('Promocodes', back_populates='quiz')

    def __str__(self):
        return f'{self.name}'


class QuizTypes(Base):
    __tablename__ = '$_quiz_types'
    __tableargs__ = {
        'comment': 'Типы квизов'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    quiz = relationship('Quizes', back_populates='type')

    def __str__(self):
        return f'{self.name}'


class QuizQuestions(Base):
    __tablename__ = '$_quiz_questions'
    __tableargs__ = {
        'comment': 'Вопросы к квизам'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    multi = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    quiz_id = Column(Integer, ForeignKey('$_quizes.id'))
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    quiz = relationship('Quizes', back_populates='quiz_questions')
    quiz_question_options = relationship('QuizQuestionOptions', back_populates='question')

    def __str__(self):
        return f'{self.title}'


class QuizQuestionOptions(Base):
    __tablename__ = '$_quiz_question_options'
    __tableargs__ = {
        'comment': 'Настройки вопросов для квиз'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    countries = Column(Text)
    for_personal_answer = Column(Integer, nullable=False)
    good = Column(Integer, nullable=False)
    question_id = Column(Integer, ForeignKey('$_quiz_questions.id'))
    replaces = Column(Text)
    title = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    question = relationship('QuizQuestions', back_populates='quiz_question_options')
    quiz_answers = relationship('QuizAnswers', back_populates='option')

    def __str__(self):
        return f'{self.title}'


class QuizBots(Base):
    __tablename__ = '$_quiz_bots'
    __tableargs__ = {
        'comment': 'Квизы бота'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('$_bots.id'))
    quiz_id = Column(Integer, ForeignKey('$_quizes.id'))
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    bot = relationship('Bots', back_populates='quiz_bots')
    quiz = relationship('Quizes', back_populates='quiz_bots')

    def __str__(self):
        return f'{self.bot_id} - {self.quiz_id}'


class QuizAttempts(Base):
    __tablename__ = '$_quiz_attempts'
    __tableargs__ = {
        'comment': 'Попытки прохождения квиза'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey('$_quizes.id'))
    status_id = Column(Integer, ForeignKey('$_quiz_attempt_statuses.id'))
    user_id = Column(Integer, ForeignKey('$_users.id'))
    rate = Column(Integer, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    quiz = relationship('Quizes', back_populates='quiz_attempts')
    status = relationship('QuizAttemptStatuses', back_populates='quiz_attempts')
    user = relationship('Users', back_populates='quiz_attempts')

    quiz_answers = relationship('QuizAnswers', back_populates='attempt')

    def __str__(self):
        return f'{self.quiz} - {self.user_id}'


class QuizAttemptStatuses(Base):
    __tablename__ = '$_quiz_attempt_statuses'
    __tableargs__ = {
        'comment': 'Статусы прохождения квиза'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    quiz_attempts = relationship('QuizAttempts', back_populates='status')

    def __str__(self):
        return f'{self.name}'


class QuizAnswers(Base):
    __tablename__ = '$_quiz_answers'
    __tableargs__ = {
        'comment': 'Ответы на квиз'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    attempt_id = Column(Integer, ForeignKey('$_quiz_attempts.id'))
    option_id = Column(Integer, ForeignKey('$_quiz_question_options.id'))
    details = Column(Text)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    attempt = relationship('QuizAttempts', back_populates='quiz_answers')
    option = relationship('QuizQuestionOptions', back_populates='quiz_answers')

    def __str__(self):
        return f'{self.attempt_id} - {self.option_id}'
