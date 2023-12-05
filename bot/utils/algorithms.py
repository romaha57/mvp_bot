from bot.quiz.models import QuizAnswers
from bot.utils.quiz_answers import (func_sociability_answer,
                                    func_sociability_text_answer)


async def func_sociability(answers: list[QuizAnswers]) -> str:
    """Обработка результатов квиза на 'Общительность' """

    # ответы пользователя(берем только смайлики)
    user_answer = []
    # счетчик совпадений ответов
    count = 0
    for i in answers:
        i = dict(i)
        user_answer.append(i['answer'])

    # если есть совпадения с ответами теста и пользовательскими, то увеличиваем счетчик
    for x, y in zip(user_answer, func_sociability_answer.values()):
        if x == y:
            count += 1

    if count > 9:
        return func_sociability_text_answer['more_9']
    elif 5 <= count <= 9:
        return func_sociability_text_answer['5-9']
    else:
        return func_sociability_text_answer['less_5']
