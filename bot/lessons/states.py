from aiogram.fsm.state import StatesGroup, State


class LessonChooseState(StatesGroup):
    """Состояния для отлова названия урока"""

    lesson = State()
    start_test = State()
    test_answer = State()
