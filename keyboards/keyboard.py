from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def get_open_context_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Открыть чат', callback_data=f'open_context_{user_id}')]
        ]
    )
    return keyboard