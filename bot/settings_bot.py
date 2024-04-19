import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Настройки всего приложения bot"""

    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.database_url_local = os.getenv('DATABASE_URL_LOCAL')
        self.log_lvl = os.getenv('LOG_LVL')
        self.debug = os.getenv('DEBUG') or 0

        if bool(int(self.debug)):
            self.bot_token = os.getenv('BOT_TOKEN_LOCAL')
        else:
            self.bot_token = os.getenv('BOT_TOKEN_MAIN')


settings = Settings()
