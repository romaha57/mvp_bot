from aiogram.fsm.state import State, StatesGroup


class GeneratePromocodeState(StatesGroup):
    """Состояния для создания промокода"""

    role = State()
    course = State()
    quiz = State()


class Anketa(StatesGroup):
    """Состояния для получение ответов пользователя на анкету"""

    answer = State()
