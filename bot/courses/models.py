from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Text,
                        func, Boolean)
from sqlalchemy.orm import relationship

from bot.db_connect import Base


class Course(Base):
    __tablename__ = '$_courses'
    __tableargs__ = {
        'comment': 'Курсы'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    intro = Column(Text, nullable=False)
    outro = Column(Text, nullable=False)
    title = Column(String)
    order_num = Column(Integer, nullable=False)
    group_id = Column(String)
    certificate_body = Column(Text)
    certificate_img = Column(Text)
    intro_video = Column(Text)
    outro_video = Column(Text)
    intro_video_type_id = Column(Integer, ForeignKey('$_video_types.id'))
    outro_video_type_id = Column(Integer, ForeignKey('$_video_types.id'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    bot_course = relationship('CourseBots', back_populates='course')
    course_history = relationship('CourseHistory', back_populates='course')

    lesson = relationship('Lessons', back_populates='course')
    promocode = relationship('Promocodes', back_populates='course')

    def __repr__(self):
        return f'{self.id} - {self.title}'


class CourseBots(Base):
    __tablename__ = '$_course_bots'
    __tableargs__ = {
        'comment': 'Курсы привязанные к боту'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('$_bots.id'))
    course_id = Column(Integer, ForeignKey('$_courses.id'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    bots_course = relationship('Bots', back_populates='bots_course')
    course = relationship('Course', back_populates='bot_course')

    def __str__(self):
        return f'{self.course_id}'


class CourseHistory(Base):
    __tablename__ = '$_course_history'
    __tableargs__ = {
        'comment': 'История прохождения курса'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('$_courses.id'))
    status_id = Column(Integer, ForeignKey('$_course_history_statuses.id'))
    user_id = Column(Integer, ForeignKey('$_users.id'))
    is_show_description = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    course = relationship('Course', back_populates='course_history')
    status = relationship('CourseHistoryStatuses', back_populates='course_history')
    user = relationship('Users', back_populates='course_history')

    lesson_history = relationship('LessonHistory', back_populates='course_history')

    def __str__(self):
        return f'{self.course_id} - {self.status_id}'


class CourseHistoryStatuses(Base):
    __tablename__ = '$_course_history_statuses'
    __tableargs__ = {
        'comment': 'Статусы истории прохождения курса'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    course_history = relationship('CourseHistory', back_populates='status')

    def __str__(self):
        return f'{self.name}'


class VideoTypes(Base):
    __tablename__ = '$_video_types'
    __tableargs__ = {
        'comment': 'Тип видео'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    lesson = relationship('Lessons', back_populates='video_type')

    def __str__(self):
        return f'{self.name}'
