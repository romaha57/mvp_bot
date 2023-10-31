from aiogram.fsm.state import StatesGroup, State


class QuizState(StatesGroup):
    """Состояние для отлова ответов на тестирование"""
    answer = State()
