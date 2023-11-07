from aiogram.fsm.state import State, StatesGroup


class LessonChooseState(StatesGroup):
    """Состояния для отлова названия урока"""

    lesson = State()
    start_test = State()
    test_answer = State()
