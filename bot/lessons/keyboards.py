from bot.lessons.service import LessonService


class LessonKeyboard:
    def __init__(self):
        self.db = LessonService()
