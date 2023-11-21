from aiogram.fsm.state import State, StatesGroup


class LessonChooseState(StatesGroup):
    """Состояния для отлова названия урока"""

    lesson = State()
    start_task = State()
    test_answer = State()
    next_lesson = State()
    task_type = State()
    text_answer = State()
    image_answer = State()
    video_answer = State()
    file_answer = State()
    circle_answer = State()
