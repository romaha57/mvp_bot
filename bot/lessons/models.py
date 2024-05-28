from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Text,
                        func)
from sqlalchemy.orm import relationship

from bot.db_connect import Base


class Lessons(Base):
    __tablename__ = '$_lessons'
    __tableargs__ = {
        'comment': 'Уроки'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    bonus_doc = Column(Text)
    description = Column(Text, nullable=False)
    order_num = Column(Integer, nullable=False)
    questions = Column(Text)
    questions_percent = Column(Integer)
    work_description = Column(Text)
    buttons_rates = Column(Text)
    course_id = Column(Integer, ForeignKey('$_courses.id'))
    work_type_id = Column(Integer, ForeignKey('$_lesson_work_types.id'))
    additional_task_id = Column(Integer, ForeignKey('$_lesson_additional_tasks.id'))
    video_type_id = Column(Integer, ForeignKey('$_video_types.id'))
    title = Column(String, nullable=False)
    video = Column(String)
    images = Column(Text)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    course = relationship('Course', back_populates='lesson')
    work_type = relationship('LessonWorkTypes', back_populates='lesson')
    lesson_history = relationship('LessonHistory', back_populates='lesson')
    test_lesson_history = relationship('TestLessonHistory', back_populates='lesson')
    additional_task = relationship('LessonAdditionalTasks', back_populates='lesson')
    video_type = relationship('VideoTypes', back_populates='lesson')

    def __str__(self):
        return f'{self.title}'


class LessonHistory(Base):
    __tablename__ = '$_lesson_history'
    __tableargs__ = {
        'comment': 'История прохождения уроков'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_history_id = Column(Integer, ForeignKey('$_course_history.id'))
    lesson_id = Column(Integer, ForeignKey('$_lessons.id'))
    status_id = Column(Integer, ForeignKey('$_lesson_history_statuses.id'))
    user_id = Column(Integer, ForeignKey('$_users.id'))
    work_details = Column(Text)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    course_history = relationship('CourseHistory', back_populates='lesson_history')
    lesson = relationship('Lessons', back_populates='lesson_history')
    status = relationship('LessonHistoryStatuses', back_populates='lesson_history')
    user = relationship('Users', back_populates='lesson_history')

    test_lesson_history = relationship('TestLessonHistory', back_populates='lesson_history')

    lesson_additional_history_task = relationship('LessonAdditionalTaskHistory', back_populates='lesson_history')

    def __str__(self):
        return f'{self.lesson_id} - {self.status_id}'


class LessonHistoryStatuses(Base):
    __tablename__ = '$_lesson_history_statuses'
    __tableargs__ = {
        'comment': 'Статуса истории уроков'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    lesson_history = relationship('LessonHistory', back_populates='status')

    def __str__(self):
        return f'{self.name}'


class TestLessonHistory(Base):
    __tablename__ = '$_test_lesson_history'
    __tableargs__ = {
        'comment': 'История тестовых вопросов к уроку'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    answers = Column(String, nullable=False)
    lesson_history_id = Column(Integer, ForeignKey('$_lesson_history.id'))
    lesson_id = Column(Integer, ForeignKey('$_lessons.id'))
    status_id = Column(Integer, ForeignKey('$_test_lesson_history_statuses.id'))
    user_id = Column(Integer, ForeignKey('$_users.id'))
    question_id = Column(Integer, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    lesson_history = relationship('LessonHistory', back_populates='test_lesson_history')
    lesson = relationship('Lessons', back_populates='test_lesson_history')
    status = relationship('TestLessonHistoryStatuses', back_populates='test_lesson_history')
    user = relationship('Users', back_populates='test_lesson_history')

    def __str__(self):
        return f'{self.lesson_id} - {self.user_id}'


class TestLessonHistoryStatuses(Base):
    __tablename__ = '$_test_lesson_history_statuses'
    __tableargs__ = {
        'comment': 'Статусы истории тестовых вопросов к уроку'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    test_lesson_history = relationship('TestLessonHistory', back_populates='status')

    def __str__(self):
        return f'{self.name}'


class LessonWorkTypes(Base):
    __tablename__ = '$_lesson_work_types'
    __tableargs__ = {
        'comment': 'Тип задания к уроку'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    lesson = relationship('Lessons', back_populates='work_type')

    def __str__(self):
        return f'{self.name}'


class LessonAdditionalTasks(Base):
    __tablename__ = '$_lesson_additional_tasks'
    __tableargs__ = {
        'comment': 'Дополнительное задание к уроку'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    description = Column(Text)
    reward = Column(Integer)
    checkup = Column(Integer)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    lesson = relationship('Lessons', back_populates='additional_task')
    lesson_additional_history_task = relationship('LessonAdditionalTaskHistory', back_populates='additional_task')

    def __str__(self):
        return f'{self.title}'


class LessonAdditionalTaskHistoryStatuses(Base):
    __tablename__ = '$_lesson_additional_task_history_statuses'
    __tableargs__ = {
        'comment': 'Типы статусов для истории прохождения доп задания'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    lesson_additional_history_task = relationship('LessonAdditionalTaskHistory', back_populates='status')

    def __str__(self):
        return f'{self.name}'


class LessonAdditionalTaskHistory(Base):
    __tablename__ = '$_lesson_additional_task_history'
    __tableargs__ = {
        'comment': 'История прохождения доп задания'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('$_users.id'))
    additional_task_id = Column(Integer, ForeignKey('$_lesson_additional_tasks.id'))
    lesson_history_id = Column(Integer, ForeignKey('$_lesson_history.id'))
    status_id = Column(Integer, ForeignKey('$_lesson_additional_task_history_statuses.id'))
    details = Column(Text)
    updated_at = Column(DateTime, onupdate=func.now)
    created_at = Column(DateTime, server_default=func.now())

    additional_task = relationship('LessonAdditionalTasks', back_populates='lesson_additional_history_task')
    user = relationship('Users', back_populates='lesson_additional_history_task')
    status = relationship('LessonAdditionalTaskHistoryStatuses', back_populates='lesson_additional_history_task')
    lesson_history = relationship('LessonHistory', back_populates='lesson_additional_history_task')

    def __str__(self):
        return f'{self.user_id} - {self.lesson_history_id}'
