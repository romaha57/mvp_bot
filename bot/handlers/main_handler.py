from bot.courses.handler import CourseHandler
from bot.handlers.command_handler import CommandHandler
from bot.handlers.text_handler import TextHandler
from bot.lessons.handler import LessonHandler
from bot.quiz.handler import QuizHandler
from bot.users.handler import UserHandler


class MainHandler:

    def __init__(self, bot):
        """Создание всех хендлеров"""

        self.bot = bot
        self.command_handler = CommandHandler(self.bot)
        self.text_handler = TextHandler(self.bot)
        self.quiz_handler = QuizHandler(self.bot)
        self.course_handler = CourseHandler(self.bot)
        self.lesson_handler = LessonHandler(self.bot)
        self.user_handler = UserHandler(self.bot)

    def handle(self):
        """Регистрация хендлеров на отлавливание сообщений"""

        self.command_handler.handle()
        self.text_handler.handle()
        self.quiz_handler.handle()
        self.course_handler.handle()
        self.lesson_handler.handle()
        self.user_handler.handle()
