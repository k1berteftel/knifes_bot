from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode, ShowMode

from database.action_data_class import DataInteraction
from states.state_groups import adminSG


context_router = Router()


@context_router.callback_query(F.data.startswith('open_context'))
async def start_context_dialog(clb: CallbackQuery, dialog_manager: DialogManager, session: DataInteraction):
    user_id = int(clb.data.split('_')[-1])
    message_ids = []
    switcher = 'me'
    dialog = await session.get_dialog(user_id)
    print(dialog)
    for message in dialog:
        print(message.__dict__)
        if switcher != 'user' and message.sender == 'user':
            msg = await clb.message.answer('<b>Сообщения от пользователя:</b>')
            message_ids.append(msg.message_id)
        if switcher != 'me' and message.sender == 'me':
            msg = await clb.message.answer('<b>Мои сообщения:</b>')
            message_ids.append(msg.message_id)
        msg = await clb.bot.copy_message(
            chat_id=clb.from_user.id,
            from_chat_id=message.user_id,
            message_id=message.message_id
        )
        message_ids.append(msg.message_id)
        switcher = message.sender
        await session.set_read(user_id)
    await session.add_context(clb.from_user.id, user_id, message_ids)
    data = {'user_id': user_id}
    if dialog_manager.has_context():
        await dialog_manager.done()
    await dialog_manager.start(adminSG.active_context, data=data, show_mode=ShowMode.DELETE_AND_SEND)