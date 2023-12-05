import requests
import uvicorn
from fastapi import FastAPI

from bot.quiz.service import QuizService
from bot.settings_bot import settings
from bot.users.service import UserService
from bot.utils.algorithms import func_sociability

app = FastAPI(
    title='API для Реалогика-Бот',
    version='1.0.0'
)


@app.get('/func_sociability')
async def func_sociability_api(
        quiz_attempt_id: int
):
    """Обработка результатов квиза(по попытке прохождения) на тему 'Общительность' """

    answers = await QuizService.get_answers_by_attempt(quiz_attempt_id)
    if answers:
        res = await func_sociability(answers)
        return res
    else:
        return 'По данной попытке не найдено ответов'


@app.post('/mailing_messages')
async def mailing_messages_api(
        message_text: str,
        users_ids: list[int]
):
    """Рассылка сообщений пользователям по их id"""

    # получаем юзеров из БД
    users = await UserService.get_users_by_id(users_ids)

    for user in users:
        url = f'https://api.telegram.org/bot{settings.bot_token}/sendMessage?chat_id={user.external_id}&parse_mode=Markdown&text={message_text}'
        requests.get(url)


if __name__ == '__main__':
    uvicorn.run('api.main:app', reload=True)
