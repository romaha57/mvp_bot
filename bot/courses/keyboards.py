from bot.courses.service import CourseService


class CourseKeyboard:
    def __init__(self):
        self.db = CourseService()
