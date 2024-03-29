import datetime

import pytz

from bot.users.models import Promocodes, Users


def is_valid_test_promo(user: Users):
    """Проверка тестового промокода по времени работы"""

    now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
    if now.replace(tzinfo=None) > user.end_test_promo.replace(tzinfo=None):
        return False
    return True
