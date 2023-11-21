import asyncio
import datetime

import requests

from bot.lessons.service import LessonService
from bot.settings_bot import settings
from bot.utils.messages import MESSAGES


async def send_message_after_30_minutes():
    """Отправляем сообщение с прохождение доп задания через 30 минут"""

    # список tg_id пользователей у кого статус в ожидании
    users_data = await LessonService.get_users_in_awaited_status()

    for record in users_data:
        if record['created_at'] + datetime.timedelta(minutes=2) <= datetime.datetime.now():
            msg = MESSAGES['CHECK_ADDITIONAL_TASK']
            url = f'https://api.telegram.org/bot{settings.bot_token}/sendMessage?chat_id={record["external_id"]}&parse_mode=Markdown&text={msg}'
            requests.get(url)

            # отмечаем статус у прохождения доп задания на 'сделан'
            await LessonService.mark_additional_task_done_status(
                additional_task_history_id=record['id']
            )

            # зачисляем бонусы пользователю
            await LessonService.add_reward_to_user(
                tg_id=record['external_id'],
                reward=record['reward'],
                comment=f'Начислено за задание: {record["title"]}'
            )

asyncio.run(send_message_after_30_minutes())
