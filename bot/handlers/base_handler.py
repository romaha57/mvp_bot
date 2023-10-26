import abc

from aiogram import Bot

from bot.services.db_service import DBService


class Handler(metaclass=abc.ABCMeta):
    """Абстрактный класс хендлера"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = DBService()

    @abc.abstractmethod
    def handle(self):
        pass
