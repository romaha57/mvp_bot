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
    'GO_TO_MENU': 'Для возврата в главное меню нажмите кнопку ниже',
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
    'ERROR': 'Прошу прощения! Произошла ошибка на сервере, пожалуйста перейдите в меню',
    'START_REFERAL': 'Система рефералов временно недоступна',
    'LOAD_RESULT_QUIZ': 'Обрабатываем ваши ответы...',
    'ANY_TEXT': 'Неизвестная команда. Выберите по кнопке ниже',
    'NO_CHOOSE_ANSWER': 'Нужно выбрать ответ',
    'TEXT_ANSWER': 'Ответь на вопрос текстом',
    'PLEASE_WRITE_CORRECT_ANSWER': 'Вы ввели неверный форма ответа',
    'YOUR_ANSWER_SAVE': 'Отлично! Ваш ответ сохранен',
    'IMAGE_ANSWER': 'Ответь на вопрос картинкой',
    'VIDEO_ANSWER': 'Ответь на вопрос видео',
    'FILE_ANSWER': 'Ответь на вопрос документом',
    'CIRCLE_ANSWER': 'Ответь на вопрос кружком',
}
