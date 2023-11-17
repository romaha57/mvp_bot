from aiogram.types import Message

from bot.quiz.models import QuizAnswers
from bot.quiz.service import QuizService


async def get_file_id_by_content_type(message: Message):
    """Получаем file_id в зависимости от типа медиа файла"""

    if message.photo:
        return message.photo[-1].file_id
    elif message.document:
        return message.document.file_id
    elif message.video:
        return message.video.file_id
    elif message.audio:
        return message.audio.file_id
    elif message.sticker:
        return message.sticker.file_id
    elif message.voice:
        return message.voice.file_id


async def format_quiz_results(answers: list[QuizAnswers.details]) -> str:
    """Формируем красивый ответ для вывода ответов пользователя на тестирование"""

    result = 'Ваши ответы:\n\n'
    date = ''
    for answer in answers:
        answer_date = answer["created_at"].strftime("%d-%m-%Y %H:%M")
        date = f'<b>Дата прохождения тестирования: {answer_date}</b>'
        result += f'{answer["question"]}\n' \
                  f'<b>{answer["answer"]}</b>\n\n'

    result = date + '\n\n' + result

    return result


async def format_answers_text(answers: list[str]):
    """Формируем сообщение вида:
    Вопрос:
    1. ответ 1
    2. ответ 2
    """
    result = ''
    letter_list = ['1', 'А', 'Б', 'В', 'Г', 'Д', 'Е']

    for number, answer in enumerate(answers, 1):
        result += f'{letter_list[number]}. '
        result += answer['title'] + '\n'

    return result


async def handle_quiz_answers(answers: list[QuizAnswers], algorithm: str):
    """Обрабатываем ответы квиза по заданному алгоритму"""
    pass
