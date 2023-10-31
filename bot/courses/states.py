from aiogram.fsm.state import StatesGroup, State


class CourseChooseState(StatesGroup):
    """Состояние для названия курса по кнопке"""

    course = State()
