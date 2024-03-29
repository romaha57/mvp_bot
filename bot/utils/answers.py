import json
import random
import string

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.courses.service import CourseService
from bot.lessons.models import Lessons
from bot.quiz.models import QuizAnswers
from bot.users.models import Promocodes
from bot.utils.algorithms import func_sociability
from bot.utils.constants import LINK
from bot.utils.messages import MESSAGES


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
    elif message.video_note:
        return message.video_note.file_id


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
    letter_list = ['1', 'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И']

    for number, answer in enumerate(answers, 1):
        result += f'{letter_list[number]}. '
        result += answer['title'] + '\n\n'

    return result


async def handle_quiz_answers(answers: list[QuizAnswers], algorithm: str):
    """Обрабатываем ответы квиза по заданному алгоритму"""

    result = ''

    if algorithm == 'func_sociability':
        result = await func_sociability(answers)

    return result


async def send_user_answers_to_group(bot: Bot, course_id: int, name: str, lesson_name: str, homework: str):
    """Отправляем ответ пользователя в соответствующую группу круса"""

    group_id = await CourseService.get_group_id(course_id)

    if group_id:
        text = MESSAGES['USER_ANSWER_IN_GROUP'].format(
            name,
            lesson_name,
            homework
        )
        try:
            await bot.send_message(group_id, text)
        except (TelegramForbiddenError, TelegramBadRequest):
            logger.warning(f'Бот не добавлен в группу: {group_id}')


async def generate_promocode(length: int = 6) -> str:
    """Генерация случайной последотвальности из 6 символов"""

    letters = string.ascii_letters
    promocode = ''.join(random.choice(letters) for i in range(length))

    return promocode


async def format_created_promocodes_text(promocodes: list[Promocodes]) -> str:
    """Формирование текста ответа с созданными промокодами"""

    answer = ''
    for promocode in promocodes:
        link = LINK + promocode.code
        answer += f'Промокод: {link}\n' \
                  f'Количество активаций: <b>{promocode.count_start}</b>\n\n'

    return answer


async def get_images_by_place(place: str, lesson: Lessons) -> list[str]:
    """Получение всех картинок для данного места (place)"""

    result_images = []
    if lesson.images:
        lesson_images = json.loads(lesson.images)

        for images_info in lesson_images:
            if images_info['place'] == place:
                result_images.append(images_info['img'])

    return result_images


async def show_lesson_info(message: Message, state: FSMContext, lesson: Lessons, user_id: int, self=None):
    """Отображение урока, используется при нажатии на 'Обучение' и при переходе из списка уроков"""

    video_text = f'<b>{lesson.title}</b>\n\n{lesson.description}'
    await state.update_data(users_answers=[])

    if lesson.video:
        try:
            # список смайликов для оценки курса

            if lesson.buttons_rates:
                self.emoji_list = json.loads(lesson.buttons_rates)

            video_msg = await message.answer_video(
                lesson.video,
                caption=video_text,
                reply_markup=await self.kb.lesson_menu_btn(lesson, self.emoji_list)
            )
            self.emoji_list = None
            # сохраняем id message, чтобы потом удалить
            await state.update_data(video_msg=video_msg.message_id)

        # отлов ошибки при неправильном file_id
        except TelegramBadRequest:
            await message.answer(
                MESSAGES['VIDEO_ERROR'],
                reply_markup=await self.kb.lesson_menu_btn(lesson)
            )

        # Отправка доп. изображений к уроку
        images = await get_images_by_place('after_video', lesson)
        if images:
            for image in images:
                try:
                    await message.answer_photo(
                        photo=image
                    )
                # отлов ошибки при неправильном file_id
                except TelegramBadRequest:
                    pass

    else:
        if lesson.buttons_rates:
            self.emoji_list = json.loads(lesson.buttons_rates)

        lesson_msg1 = await message.answer(
            video_text,
            reply_markup=await self.kb.lesson_menu_btn(lesson, self.emoji_list)
        )
        self.emoji_list = None
        # сохраняем message_id, чтобы потом их удалить
        await state.update_data(lesson_msg1=lesson_msg1.message_id)

    # получаем актуальную попытку прохождения урока
    actual_lesson_history = await self.db.get_actual_lesson_history(
        user_id=user_id,
        lesson_id=lesson.id
    )
    await state.update_data(lesson_history_id=actual_lesson_history.id)
    await state.update_data(chat_id=message.chat.id)


def collect_query_for_knowledge_base(divides_ids: str, file_ids) -> tuple[str, str]:
    """Собираем запрос для кнопки 'назад' в меню базы знаний """

    divide_query = ''
    file_query = ''

    if divides_ids:
        divides_ids = tuple([int(item) for item in divides_ids.split(',')])
        if len(divides_ids) == 1:
            divide_query = f" id = {divides_ids[0]} "
        else:
            divide_query = f" id IN {divides_ids} "

    if file_ids:
        file_ids = tuple([int(item) for item in file_ids.split(',')])
        if len(file_ids) == 1:
            file_query = f" id = {file_ids[0]} "
        else:
            file_query = f" id IN {file_ids} "

    return divide_query, file_query
