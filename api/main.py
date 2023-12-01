import datetime

from fastapi import FastAPI

from api.schemas import StrResponse
from bot.quiz.service import QuizService
from bot.utils.algorithms import func_sociability


app = FastAPI(
    title='API для Реалогика-Бот',
    version='1.0.0'
)


@app.get('/func_sociability', response_model=StrResponse)
async def func_sociability_api(
        quiz_attempt_id: int
):
    answers = await QuizService.get_answers_by_attempt(quiz_attempt_id)
    return await func_sociability(answers)
