from typing import Union

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message


async def delete_messages(data: dict, state: FSMContext, src: Union[CallbackQuery, Message, Bot]):
    """Проверяем наличие сообщение с кнопкой и удаляем его"""

    try:
        if isinstance(src, Bot):
            # убираем кнопки управление уроком(Назад, Выполнить задание)
            if data.get('video_msg'):
                await src.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('video_msg')
                )
                await state.update_data(video_msg=None)

            # убираем кнопки управление уроком(Назад, Выполнить задание)
            if data.get('lesson_msg1'):
                await src.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('lesson_msg1')
                )
                await state.update_data(lesson_msg1=None)

            if data.get('msg1'):
                await src.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('msg1')
                )
                await state.update_data(msg1=None)

            if data.get('msg2'):
                await src.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('msg2')
                )
                await state.update_data(msg2=None)

            if data.get('delete_test_message'):
                await src.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('delete_test_message')
                )
                await state.update_data(delete_test_message=None)

            if data.get('delete_message_id') and data.get('chat_id'):
                await src.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('delete_message_id')
                )

                await state.update_data(delete_message_id=None)

            if data.get('menu_msg'):
                await src.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('menu_msg')
                )

                await state.update_data(menu_msg=None)

            if data.get('quiz_result_msg'):
                await src.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('quiz_result_msg')
                )

                await state.update_data(quiz_result_msg=None)

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
        else:

            if data.get('video_msg'):
                await src.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('video_msg')
                )
                await state.update_data(video_msg=None)
            # убираем кнопки управление уроком(Назад, Выполнить задание)
            if data.get('video_description_msg'):
                await src.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('video_description_msg')
                )
                await state.update_data(video_description_msg=None)

            # убираем кнопки управление уроком(Назад, Выполнить задание)
            if data.get('lesson_msg1'):
                await src.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('lesson_msg1')
                )
                await state.update_data(lesson_msg1=None)

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

            if data.get('base_msg'):
                await src.bot.delete_message(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('base_msg')
                )
                await state.update_data(base_msg=None)
    except Exception:
        pass
