from typing import Union

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message


async def delete_messages(data: dict, state: FSMContext, src: Union[Message, Bot]):
    """Проверяем наличие сообщение с кнопкой и удаляем его"""

    if isinstance(src, Message):
        src = src.bot

    # убираем кнопки управление уроком(Назад, Выполнить задание)
    if data.get('msg_edit'):
        await src.edit_message_reply_markup(
            chat_id=data.get('chat_id'),
            message_id=data.get('msg_edit')
        )
        await state.update_data(msg_edit=None)

    try:
        if data.get('msg'):
            await src.edit_message_reply_markup(
                chat_id=data.get('chat_id'),
                message_id=data.get('msg'),
                reply_markup=None
            )
            await state.update_data(msg=None)
    except Exception:
        if data.get('msg'):
            await src.delete_message(
                chat_id=data.get('chat_id'),
                message_id=data.get('msg'),
            )
            await state.update_data(msg=None)

    if data.get('msg1'):
        await src.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('msg1'),
        )
        await state.update_data(msg1=None)

    if data.get('delete_test_message'):
        await src.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('delete_test_message')
        )
        await state.update_data(delete_test_message=None)

    if data.get('additional_msg'):
        await src.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('additional_msg')
        )

        await state.update_data(additional_msg=None)

    if data.get('base_msg'):
        await src.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('base_msg')
        )

        await state.update_data(base_msg=None)

