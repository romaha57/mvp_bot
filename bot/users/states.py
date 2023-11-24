from aiogram.fsm.state import State, StatesGroup


class GeneratePromocodeState(StatesGroup):
    """Состояния для создания промокода"""

    role = State()
    course = State()
    quiz = State()
