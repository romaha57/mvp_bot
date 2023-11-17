from typing import Union

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message


async def delete_messages(data: dict, state: FSMContext, src: Union[CallbackQuery, Message]):
    """Проверяем наличие сообщение с кнопкой и удаляем его"""

    if data.get('video_msg'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('video_msg')
        )
        await state.update_data(video_msg=None)

    if data.get('video_description_msg'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('video_description_msg')
        )
        await state.update_data(video_description_msg=None)

    if data.get('msg1'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('msg1')
        )
        await state.update_data(msg1=None)

    if data.get('msg2'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('msg2')
        )
        await state.update_data(msg2=None)

    if data.get('delete_test_message'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('delete_test_message')
        )
        await state.update_data(delete_test_message=None)

    if data.get('delete_message_id') and data.get('chat_id'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('delete_message_id')
        )

        await state.update_data(delete_message_id=None)

    if data.get('menu_msg'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('menu_msg')
        )

        await state.update_data(menu_msg=None)

    if data.get('quiz_result_msg'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('quiz_result_msg')
        )

        await state.update_data(quiz_result_msg=None)

    if data.get('additional_msg'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('additional_msg')
        )

        await state.update_data(additional_msg=None)