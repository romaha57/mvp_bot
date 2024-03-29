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

fail_test_text = """
Твой результат <b>{}</b> %

К сожалению, ты не прошел 🙁
Для успешного выполнения задания нужно ответить правильно минимум на <b>{}</b> % вопросов.

Пересмотри урок еще раз и попробуй пройти тест заново. У тебя все получится!

"""

MESSAGES = {
    'KB_PLACEHOLDER': 'Выберите одну из функций',
    'QUIZ_ANSWERS': 'Выберите ответ по кнопке',
    'ERROR_PROMOCODE': 'Ошибка чтения промокода! Попробуйте перейти по ссылку приглашению еще раз',
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
    'TEST_QUESTION': test_question_text,
    'SUCCESS_TEST': 'Поздравляем! Вы прошли тест. Ваш результат {}%',
    'FAIL_TEST': fail_test_text,
    'ALL_LESSONS_DONE': 'Все уроки в этом курсе завершены',
    'NEXT_LESSON': 'Следующий урок ➡️',
    'CORRECT_ANSWER': '<b>Отлично! Вы ответили верно</b>',
    'INCORRECT_ANSWER': incorrect_answer_text,
    'ERROR': 'Прошу прощения! Произошла ошибка на сервере, пожалуйста перейдите в меню',
    'START_REFERAL': 'Система рефералов временно недоступна',
    'LOAD_RESULT_QUIZ': 'Обрабатываем ваши ответы...',
    'ANY_TEXT': 'Неизвестная команда. Выберите по кнопке ниже',
    'NO_CHOOSE_ANSWER': 'Нужно выбрать ответ',
    'PLEASE_WRITE_CORRECT_ANSWER': 'Вы ввели неверный форма ответа',
    'YOUR_ANSWER_SAVE': 'Отлично! Твой ответ сохранен',
    'CALCULATE_RESULT': 'Ваш результат обработан по алгоритму {}',
    'ADDITIONAL_TASK': 'Дополнительное задание к уроку: \n{}',
    'ADD_REWARD_AFTER_TIME': 'Cпасибо за выполнение! Администратор проверит и по результат отправим вам сообщение)',
    'REWARDS_WAS_ADDED': 'Отлично! Бонусы зачислены вам в кошелек',
    'CHECK_ADDITIONAL_TASK': 'Поздравляем! Мы проверили ваше задание и начислили вам бонусы)',
    'BALANCE': 'Данный раздел пока разработке, скоро начнешь тратить на разные крутые плюшки',
    'USER_ANSWER_IN_GROUP': 'Пользователь: <b>{}</b> \nУрок: <b>{}</b>\nДЗ: <b>{}</b>',
    'MANAGER_PANEL': 'Панель менеджера',
    'INCORRECT_PROMOCODE_COURSE': 'Неверено выбран курс',
    'INCORRECT_PROMOCODE_ROLE': 'Неверено выбрана роль',
    'INCORRECT_PROMOCODE_QUIZ': 'Неверено выбран квиз',
    'INCORRECT_FIO': 'Неверено задано ФИО',
    'CREATED_PROMOCODE': 'Промокод успешно создан: <b>{}</b>',
    'WRONG_PROMOCODE': 'Неверный промокод! Обратитесь в поддержку: ссылка на поддержку',
    'CERTIFICATE': 'Формируем ваш сертификат',
    'VIDEO_ERROR': 'Не удалось отправить видео',
    'QUIZ_SELECTION': 'Меню тестирования',
    'KNOWLEDGE_MENU': 'Доступные материалы Базы Знаний:',
    'ADD_YOUR_FULLNAME': 'Для выдачи сертификата об успешном прохождении курса введите, пожалуйста, ваше ФИО',
    'ERROR_IN_HANDLER': 'Произошла ошибка! Пожалуйста, перезапустите бота по кнопке или перейдите ссылке с промокодом',
    'SOME_ERROR': 'Произошла неизвестная ошибка на сервере! Пожалуйста сообщите службе поддержке: @justagreeny'
}
