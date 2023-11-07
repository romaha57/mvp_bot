from aiogram.fsm.state import State, StatesGroup


class CourseChooseState(StatesGroup):
    """Состояние для названия курса по кнопке"""

    course = State()
