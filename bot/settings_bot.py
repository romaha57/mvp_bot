import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Настройки всего приложения bot"""

    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.log_lvl = os.getenv('LOG_LVL')
        self.bot_token = os.getenv('BOT_TOKEN')


settings = Settings()
