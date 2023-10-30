from aiogram.fsm.state import StatesGroup, State


class QuizState(StatesGroup):
    quiz_id = State()
    question = State()
    answer = State()
