from aiogram.fsm.state import State, StatesGroup


class QuizState(StatesGroup):
    """Состояние для отлова ответов на тестирование"""

    answer = State()
    quiz = State()
