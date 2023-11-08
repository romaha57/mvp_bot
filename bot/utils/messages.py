result_quiz_text = """
{}
Ответ: <b>{}</b>
"""

test_question_text = """
{}
{}
"""

incorrect_answer_text = """
Ошибка! Правильный ответ: 
<b>{}</b>
"""


MESSAGES = {
    'KB_PLACEHOLDER': 'Выберите одну из функций',
    'QUIZ_ANSWERS': 'Выберите ответ по кнопке',
    'MENU': 'Главное меню',
    'GO_TO_MENU': 'Вернуться в меню?',
    'CHOOSE_LESSONS': 'Выберите урок',
    'LESSONS_LIST': 'Список уроков',
    'CHOOSE_COURSE': 'Выберите курс',
    'RESULTS_QUIZ': result_quiz_text,
    'NOT_FOUND_COURSE': 'Таково курса не существует, выберите его из списка ниже',
    'NOT_FOUND_LESSON': 'Таково урока не существует, выберите его из списка ниже',
    'START_TEST': 'Начат тест',
    'END_TEST': 'Вы завершили тест. правильных ответов: {}',
    'START_CALCULATE_TEST_RESULTS': 'Производим подсчет ваших результатов',
    'TEST_QUESTION': test_question_text,
    'SUCCESS_TEST': 'Поздравляем! Вы прошли тест. Ваш результат {}',
    'FAIL_TEST': 'К сожалению, вы не прошли тест',
    'ALL_LESSONS_DONE': 'Все уроки в этом курсе завершены',
    'NEXT_LESSON': 'Перейдем к следующему уроку',
    'CORRECT_ANSWER': 'Отлично! Вы ответили верно',
    'INCORRECT_ANSWER': incorrect_answer_text,
}
