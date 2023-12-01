import datetime

from fastapi import FastAPI

from bot.utils.algorithms import func_sociability


app = FastAPI(
    title='API для Реалогика-Бот',
    version='1.0.0'
)


mock_answers = [{'question': '❓ Вопрос: В свободное время я стараюсь быть среди людей', 'answer': '✅', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 26)}, {'question': '❓ Вопрос: Доверие к людям чаще приводит к неприятностям', 'answer': '❌', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 28)}, {'question': '❓ Вопрос: В жизни важнее самостоятельность или независимость, чем умение понимать других людей', 'answer': '✅', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 29)}, {'question': '❓ Вопрос: Я люблю шумные и веселые компании', 'answer': '❌', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 30)}, {'question': '❓ Вопрос: Я хорошо запоминаю имена и лица новых знакомых', 'answer': '✅', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 31)}, {'question': '❓ Вопрос: У меня часто возникает желание помочь другим', 'answer': '❌', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 33)}, {'question': '❓ Вопрос: Мне трудно вести себя с людьми естественно и непринужденно', 'answer': '✅', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 34)}, {'question': '❓ Вопрос: Я люблю что-то организовывать для других', 'answer': '❌', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 35)}, {'question': '❓ Вопрос: Меня раздражает откровенность и многословность некоторых знакомых', 'answer': '✅', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 36)}, {'question': '❓ Вопрос: Часто я могу понять настроения и желания незнакомых мне людей', 'answer': '❌', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 38)}, {'question': '❓ Вопрос: Я обычно трудно схожусь и знакомлюсь с новыми людьми', 'answer': '✅', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 39)}, {'question': '❓ Вопрос: Меня мало интересует личная жизнь моих знакомых', 'answer': '❌', 'created_at': datetime.datetime(2023, 12, 1, 9, 55, 40)}]


@app.get('/func_sociability')
async def func_sociability_api():
    return await func_sociability(mock_answers)
