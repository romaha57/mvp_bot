import json
import pprint
import random
import string
from typing import Union

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.courses.models import Course, CourseHistory
from bot.courses.service import CourseService
from bot.lessons.models import Lessons
from bot.quiz.models import QuizAnswers
from bot.test_promocode.utils import is_valid_test_promo
from bot.users.models import Promocodes, Users
from bot.users.service import UserService
from bot.users.states import Politics
from bot.utils.algorithms import func_sociability
from bot.utils.constants import LINK
from bot.utils.messages import MESSAGES


async def get_file_id_by_content_type(message: Message):
    """Получаем file_id в зависимости от типа медиа файла"""

    if message.photo:
        return message.photo[-1].file_id, 1, message.caption
    elif message.document:
        return message.document.file_id, 4, message.caption
    elif message.video:
        return message.video.file_id, 2, message.caption
    elif message.audio:
        return message.audio.file_id, 3, message.caption
    elif message.sticker:
        return message.sticker.file_id, 5, message.caption
    elif message.voice:
        return message.voice.file_id, 7, message.caption
    elif message.video_note:
        return message.video_note.file_id, 6, message.caption


async def send_image(lesson: Lessons, message: Message, place: str):
    images = await get_images_by_place(place, lesson)
    if images:
        for image in images:
            try:
                await message.answer_photo(
                    photo=image
                )
            # отлов ошибки при неправильном file_id
            except TelegramBadRequest:
                pass


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

    await send_image(lesson, message, 'before_video')

    if lesson.video:

        if lesson.buttons_rates:
            self.emoji_list = json.loads(lesson.buttons_rates)

        try:
            msg = await message.answer_video(
                lesson.video,
                caption=video_text,
                reply_markup=await self.kb.lesson_menu_btn(lesson, self.emoji_list)
            )

        except TelegramBadRequest as e:
            msg = await message.answer(
                MESSAGES['VIDEO_ERROR'],
                reply_markup=await self.kb.lesson_menu_btn(lesson)
            )
            self.emoji_list = None
            logger.warning(f'Не удалось отправить видео: {e}')

        await state.update_data(msg_edit=msg.message_id)

    else:
        if lesson.buttons_rates:
            self.emoji_list = json.loads(lesson.buttons_rates)

        msg = await message.answer(
            video_text,
            reply_markup=await self.kb.lesson_menu_btn(lesson, self.emoji_list)
        )
        self.emoji_list = None
        await state.update_data(msg_edit=msg.message_id)

    await send_image(lesson, message, 'after_video')


async def show_course_intro_first_time(course: Course, message: Message, state: FSMContext,
                                 self: 'CourseHandler', course_history: CourseHistory, user_id: int, promocode: Promocodes):
    if course.intro_video:
        try:
            await message.answer_video(
                video=course.intro_video
            )
        except TelegramBadRequest as e:
            if 'VOICE_MESSAGES_FORBIDDEN' in e.message:
                await message.answer(
                    MESSAGES['VIDEO_ERROR_FORBIDDEN']
                )
            else:
                await message.answer(
                    MESSAGES['VIDEO_ERROR']
                )
                logger.warning(f'Не удалось отправить видео {message.chat.id} -- {e.message}')

    await message.answer(course.title)
    msg = await message.answer(
        course.intro,
        reply_markup=await self.lesson_kb.lessons_btn(course.id, user_id, promocode)
    )
    await state.update_data(msg=msg.message_id)
    await self.db.mark_show_course_description(course_history, False)


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


async def check_user_anket(message: Message, user: Users):
    """Проверка на неотвеченные вопросы на анкеты пользователя"""

    account = await UserService.get_account_by_tg_id(message.chat.id)
    account_id = account.id
    questions = await UserService.get_unanswered_questions(account_id)
    if questions:
        return questions


async def show_main_menu(promocode: Promocodes, user: Users, message: Message, state: FSMContext, self: Union['TextHandler', 'MainBot']):

    if user.accept_politics:

        if promocode.is_test:
            if is_valid_test_promo(user):
                await message.answer(
                    MESSAGES['TEST_PROMO_MENU'],
                    reply_markup=await self.test_promo_kb.test_promo_menu()
                )

            else:
                await message.answer(
                    MESSAGES['END_TEST_PERIOD'],
                    reply_markup=await self.test_promo_kb.test_promo_menu()
                )
                await state.set_state(state=None)

        elif promocode.type_id == 3:
            await message.answer(
                MESSAGES['MENU'],
                reply_markup=await self.kb.start_btn(promocode))

        else:
            courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
            await message.answer(
                MESSAGES['ANY_TEXT'],
                reply_markup=await self.kb.start_btn(courses_and_quizes)
            )

    else:
        msg = await message.answer(
            MESSAGES['ACCEPT_POLITICS'],
            reply_markup=await self.kb.politics_btn()
        )
        await state.set_state(Politics.accept)
        await state.update_data(msg=msg.message_id)


async def check_new_added_lessons(lessons_by_user: list[dict], lessons_by_course: list[dict], user_id: int, all_lesson: bool = False) -> list[dict]:
    lessons_by_user_list = [
        (
            lesson.get('id'),
            lesson.get('title'),
            lesson.get('order_num')
        )

        for lesson in lessons_by_user
    ]
    lessons_by_course_list = [
        (
            lesson.get('id'),
            lesson.get('title'),
            lesson.get('order_num')
        )
        for lesson in lessons_by_course
    ]
    new_lessons = list(set(lessons_by_course_list) - set(lessons_by_user_list))

    if all_lesson:
        for new_l in new_lessons:
            lessons_by_user.append(
                {
                    'id': new_l[0],
                    'title': new_l[1],
                    'order_num': new_l[2],
                    'user_id': user_id,
                    'status_id': 0
                }
            )

    else:
        _max_user_lessons = sorted(lessons_by_user_list, key=lambda lesson: lesson[2], reverse=True)
        max_user_lesson_order_num = _max_user_lessons[0][2]
        for new_l in new_lessons:
            if new_l[2] < max_user_lesson_order_num:
                lessons_by_user.append(
                    {
                        'id': new_l[0],
                        'title': new_l[1],
                        'order_num': new_l[2],
                        'user_id': user_id,
                        'status_id': 0
                    }
                )

    return lessons_by_user


async def catch_menu_btn_in_answers(self: 'LessonHandler', message: Message, state: FSMContext, tg_id: int):
    promocode = await self.db.get_promocode_by_tg_id(tg_id)

    await state.set_state(state=None)

    if promocode.type_id == 3:
        await message.answer(
            MESSAGES['MENU'],
            reply_markup=await self.kb.start_btn(promocode))

    else:
        courses_and_quizes = await self.db.get_promocode_courses_and_quizes(promocode.id)
        await message.answer(
            MESSAGES['MENU'],
            reply_markup=await self.kb.start_btn(courses_and_quizes)
        )
