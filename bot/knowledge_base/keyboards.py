from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.knowledge_base.service import KnowledgeService
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class KnowledgeKeyboard:
    def __init__(self):
        self.db = KnowledgeService()

    def divides_menu(self, root_divides: list[dict], files: list[dict] = None) -> InlineKeyboardMarkup:
        """Кнопки с меню базы знаний"""

        builder = InlineKeyboardBuilder()
        back_button = False

        if root_divides:
            for divide in root_divides:
                name = divide.get('title')
                id = divide.get('id')
                builder.row(
                    InlineKeyboardButton(
                        text=f'📂 {name}',
                        callback_data=f'divide_{id}'
                    ))

                if divide.get('parent_id'):
                    back_button = divide.get('parent_id')

        if files:

            for file in files:
                name = file.get('title')
                id = file.get('id')
                type = file.get('type_id')

                if type == 3:
                    builder.row(
                        InlineKeyboardButton(
                            text=f'🔗 {name}',
                            url=file.get('document')
                        ))

                elif type == 2:
                    builder.row(
                        InlineKeyboardButton(
                            text=f'🎥 {name}',
                            callback_data=f'file_{id}'
                        ))
                else:
                    builder.row(
                        InlineKeyboardButton(
                            text=f'📄 {name}',
                            callback_data=f'file_{id}'
                        ))

                if file.get('parent_id'):
                    back_button = int(file.get('parent_id')) + 1

        if back_button:
            builder.row(
                InlineKeyboardButton(
                    text=BUTTONS['BACK_BASE'],
                    callback_data=f'baseback_{back_button}'
                )
            )

        builder.row(
            InlineKeyboardButton(
                text=BUTTONS['MENU'],
                callback_data='menu'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
