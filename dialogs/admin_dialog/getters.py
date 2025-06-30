import os
import datetime

from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.build_ids import get_random_id
from utils.schedulers import send_messages
from database.action_data_class import DataInteraction
#from database.model import DialogsTable
from config_data.config import load_config, Config
from states.state_groups import adminSG


async def get_static(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    users = await session.get_users()
    active = 0
    entry = {
        'today': 0,
        'yesterday': 0,
        '2_day_ago': 0
    }
    activity = 0
    for user in users:
        if user.active:
            active += 1
        for day in range(0, 3):
            #print(user.entry.date(), (datetime.datetime.today() - datetime.timedelta(days=day)).date())
            if user.entry.date() == (datetime.datetime.today() - datetime.timedelta(days=day)).date():
                if day == 0:
                    entry['today'] = entry.get('today') + 1
                elif day == 1:
                    entry['yesterday'] = entry.get('yesterday') + 1
                else:
                    entry['2_day_ago'] = entry.get('2_day_ago') + 1
        if user.activity.timestamp() > (datetime.datetime.today() - datetime.timedelta(days=1)).timestamp():
            activity += 1

    text = (f'<b>Статистика на {datetime.datetime.today().strftime("%d-%m-%Y")}</b>\n\nВсего пользователей: {len(users)}'
            f'\n - Активные пользователи(не заблокировали бота): {active}\n - Пользователей заблокировали '
            f'бота: {len(users) - active}\n - Провзаимодействовали с ботом за последние 24 часа: {activity}\n\n'
            f'<b>Прирост аудитории:</b>\n - За сегодня: +{entry.get("today")}\n - Вчера: +{entry.get("yesterday")}'
            f'\n - Позавчера: + {entry.get("2_day_ago")}')
    await clb.message.answer(text=text)


async def queues_menu_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    queues = await session.get_queues()
    text = ''
    for queue in queues:
        text += (f'<b>ID:</b> {queue.id} (<em>{queue.name}</em>), отправляется через '
                 f'{queue.minutes // 60} часов {queue.minutes % 60} минут:\n')
    return {
        'text': text if text else 'Отсутствуют',
        'queues': bool(queues)
    }


async def get_queue_message(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data['message_id'] = msg.message_id
    dialog_manager.dialog_data['chat_id'] = msg.chat.id
    await dialog_manager.switch_to(adminSG.get_queue_name)


async def get_queue_name(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['name'] = text
    await dialog_manager.switch_to(adminSG.get_queue_time)


async def get_queue_time(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        fragment = text.split(':')
        hour = int(fragment[0])
        minutes = int(fragment[1])
    except Exception:
        await msg.answer('Вы ввели время не в том формате, пожалуйста попробуйте еще раз')
        await msg.delete()
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    name = dialog_manager.dialog_data.get('name')
    message_id = dialog_manager.dialog_data.get('message_id')
    chat_id = dialog_manager.dialog_data.get('chat_id')
    await session.add_queue(name, message_id, chat_id, hour * 60 + minutes)
    await msg.answer('Отложенное сообщение было успешно добавлено')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.queues_menu)


async def del_queue_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    queues = await session.get_queues()
    buttons = []
    for queue in queues:
        buttons.append(
            (queue.name, queue.id)
        )
    return {'items': buttons}


async def del_queue_selector(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    queue = await session.get_queue(int(item_id))
    msg = await clb.bot.copy_message(
        message_id=queue.message_id,
        chat_id=clb.from_user.id,
        from_chat_id=queue.chat_id
    )
    dialog_manager.dialog_data['msg_id'] = msg.message_id
    dialog_manager.dialog_data['queue_id'] = int(item_id)
    await dialog_manager.switch_to(adminSG.confirm_del_queue, show_mode=ShowMode.DELETE_AND_SEND)


async def del_queue(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    queue_id = dialog_manager.dialog_data.get('queue_id')
    msg_id = dialog_manager.dialog_data.get('msg_id')
    try:
        await clb.bot.delete_message(
            clb.from_user.id,
            msg_id
        )
    except Exception:
        ...
    await session.del_queue(queue_id)
    await clb.answer('Отложенное сообщение было успешно удаленно')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.del_queue)


async def del_queue_switcher(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    msg_id = dialog_manager.dialog_data.get('msg_id')
    try:
        await clb.bot.delete_message(
            clb.from_user.id,
            msg_id
        )
    except Exception:
        ...
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.del_queue)


async def dialog_pager(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    if clb.data.startswith('next'):
        dialog_manager.dialog_data['page'] = dialog_manager.dialog_data.get('page') + 1
    else:
        dialog_manager.dialog_data['page'] = dialog_manager.dialog_data.get('page') - 1
    await dialog_manager.switch_to(adminSG.choose_dialog)


async def choose_dialog_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    text = (f'Выберите пользователя с которым вы хотели бы продолжить диалог\n\n<b>Важно!</b>\n<em>'
            f'🟢 - Вы прочитали и ответили на сообщения пользователю\n'
            f'🟡 - Вы прочитали и НЕ ответили на сообщение пользователя\n'
            f'🔴 - Вы НЕ прочитали и НЕ ответили на сообщение пользователя\n'
            f'(01:00) - время в часах и минутах, в течение которого вы НЕ отвечали на сообщение от пользователя</em>')
    dialogs = dialog_manager.dialog_data.get('dialogs')
    if not dialogs:
        dialogs = []
        users = await session.get_users()
        for i in range(3):
            for user in users:
                dialog = []#list[DialogsTable] = user.dialogs  # отсортировать массив по дате
                time: datetime.timedelta = (datetime.datetime.today() - dialog[-1].date)
                print(datetime.datetime.today(), dialog[-1].date, dialog[-1].user_id)
                minutes = round(time.total_seconds() % 60)
                if len(str(minutes)) != 2:
                    minutes =('0' + str(minutes))
                time: str = f'{round(time.total_seconds() // 3600)}:{minutes}'
                if i == 0:
                    if False in [data.read for data in dialog] and dialog[-1].sender == 'user':
                        dialogs.append((f'🔴({time}):{user.username}|{user.user_id}', user.user_id))  # перевод всего времени в часы и минуты
                if i == 1:
                    if False not in [data.read for data in dialog] and dialog[-1].sender == 'user':
                        dialogs.append((f'🟡({time}):{user.username}|{user.user_id}', user.user_id))
                if i == 2:
                    if False not in [data.read for data in dialog] and dialog[-1].sender == 'me':
                        dialogs.append((f'🟢:{user.username}|{user.user_id}', user.user_id))
        dialogs = [dialogs[i:i + 20] for i in range(0, len(dialogs), 20)]
        dialog_manager.dialog_data['dialog'] = dialogs

    page = dialog_manager.dialog_data.get('page')
    if page is None:
        page = 0
        dialog_manager.dialog_data['page'] = page
    not_first = True
    not_last = True
    if page == 0:
        not_first = False
    if len(dialogs) - 1 <= page:
        not_last = False
    print(dialogs)
    return {
        'text': text,
        'not_first': not_first,
        'not_last': not_last,
        'pages': f'{page}/{len(dialogs)}',
        'items': dialogs[page]
    }


async def dialog_selector(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user_id = int(item_id)
    message_ids = []
    switcher = 'me'
    dialog = await session.get_dialog(user_id)
    for message in dialog:
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
    dialog_manager.dialog_data['user_id'] = user_id
    await dialog_manager.switch_to(adminSG.active_context, show_mode=ShowMode.DELETE_AND_SEND)


async def search_dialog(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        user_id = int(text)
    except Exception:
        if not text.startswith('@'):
            await msg.answer('Юзернейм должен начинаться с @, пожалуйста попробуйте снова')
            return
        user_id = text
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    if isinstance(user_id, int):
        user = await session.get_user(user_id)
        if not user:
            await msg.answer('К сожалению пользователя с таким ID не было найденно')
            return
    else:
        user = await session.get_user_by_username(user_id[1::])
        if not user:
            await msg.answer('К сожалению пользователя с таким юзернеймом не было найдено')
            return
    user_id = user.user_id
    message_ids = []
    switcher = 'me'
    dialog = await session.get_dialog(user_id)
    for message in dialog:
        if switcher != 'user' and message.sender == 'user':
            mess = await msg.answer('<b>Сообщения от пользователя:</b>')
            message_ids.append(mess.message_id)
        if switcher != 'me' and message.sender == 'me':
            mess = await msg.answer('<b>Мои сообщения:</b>')
            message_ids.append(mess.message_id)
        mess = await msg.bot.copy_message(
            chat_id=msg.chat.id,
            from_chat_id=message.user_id,
            message_id=message.message_id
        )
        message_ids.append(mess.message_id)
        switcher = message.sender
        await session.set_read(user_id)
    await session.add_context(msg.from_user.id, user_id, message_ids)
    dialog_manager.dialog_data['user_id'] = user_id
    await dialog_manager.switch_to(adminSG.active_context, show_mode=ShowMode.DELETE_AND_SEND)


async def get_context_message(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user_id = dialog_manager.dialog_data.get('user_id')
    if not user_id:
        user_id = dialog_manager.start_data.get('user_id')
        dialog_manager.dialog_data['user_id'] = user_id
    try:
        message = await msg.bot.copy_message(user_id, msg.from_user.id, msg.message_id)
    except Exception:
        message = await msg.answer('Произошла какая-то ошибка при отправке сообщения, '
                                   'скорее всего пользователь заблокировал бота')
        await session.add_context_message_ids(user_id, msg.from_user.id, [msg.message_id, message.message_id])
        return
    await session.add_dialog_message(user_id, message.message_id, 'me', read=True)
    message_2 = await msg.reply('✅Доставлено')
    await session.add_context_message_ids(user_id, msg.from_user.id, [msg.message_id, message_2.message_id])
    await dialog_manager.switch_to(adminSG.active_context, show_mode=ShowMode.DELETE_AND_SEND)


async def close_dialog(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user_id = dialog_manager.dialog_data.get('user_id')
    if not user_id:
        user_id = dialog_manager.start_data.get('user_id')
        dialog_manager.dialog_data['user_id'] = user_id
    context = await session.get_admin_context(user_id, clb.from_user.id)
    for message_id in context.message_ids:
        try:
            await clb.bot.delete_message(clb.from_user.id, message_id)
        except Exception:
            ...
    await session.del_user_context(clb.from_user.id, user_id)
    dialog_manager.dialog_data.clear()
    if dialog_manager.start_data:
        dialog_manager.start_data.clear()
    await dialog_manager.switch_to(adminSG.start)


async def get_users_txt(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    users = await session.get_users()
    with open('users.txt', 'a+') as file:
        for user in users:
            file.write(f'{user.user_id}\n')
    await clb.message.answer_document(
        document=FSInputFile(path='users.txt')
    )
    try:
        os.remove('users.txt')
    except Exception:
        ...


async def deeplink_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    links = await session.get_deeplinks()
    text = ''
    for link in links:
        text += f'https://t.me/bot?start={link.link}: {link.entry}\n'  # Получить ссылку на бота и поменять
    return {'links': text}


async def add_deeplink(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.add_deeplink(get_random_id())
    await dialog_manager.switch_to(adminSG.deeplink_menu)


async def del_deeplink(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_deeplink(item_id)
    await clb.answer('Ссылка была успешно удаленна')
    await dialog_manager.switch_to(adminSG.deeplink_menu)


async def del_deeplink_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    links = await session.get_deeplinks()
    buttons = []
    for link in links:
        buttons.append((f'{link.link}: {link.entry}', link.link))
    return {'items': buttons}


async def del_admin(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_admin(int(item_id))
    await clb.answer('Админ был успешно удален')
    await dialog_manager.switch_to(adminSG.admin_menu)


async def admin_del_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    admins = await session.get_admins()
    buttons = []
    for admin in admins:
        buttons.append((admin.name, admin.user_id))
    return {'items': buttons}


async def refresh_url(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    id: str = dialog_manager.dialog_data.get('link_id')
    dialog_manager.dialog_data.clear()
    await session.del_link(id)
    await dialog_manager.switch_to(adminSG.admin_add)


async def admin_add_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    id = get_random_id()
    dialog_manager.dialog_data['link_id'] = id
    await session.add_link(id)
    return {'id': id}


async def admin_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    admins = await session.get_admins()
    text = ''
    for admin in admins:
        text += f'{admin.name}\n'
    return {'admins': text}


async def get_mail(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    if msg.text:
        dialog_manager.dialog_data['text'] = msg.html_text
    elif msg.photo:
        dialog_manager.dialog_data['photo'] = msg.photo[0].file_id
        dialog_manager.dialog_data['caption'] = msg.html_text
    elif msg.video:
        dialog_manager.dialog_data['video'] = msg.video.file_id
        dialog_manager.dialog_data['caption'] = msg.html_text
    else:
        await msg.answer('Что-то пошло не так, пожалуйста попробуйте снова')
    await dialog_manager.switch_to(adminSG.get_time)


async def get_time(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        time = datetime.datetime.strptime(text, '%H:%M %d.%m')
    except Exception as err:
        print(err)
        await msg.answer('Вы ввели данные не в том формате, пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['time'] = text
    await dialog_manager.switch_to(adminSG.get_keyboard)


async def get_mail_keyboard(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        buttons = text.split('\n')
        keyboard: list[tuple] = [(i.split('-')[0].strip(), i.split('-')[1].strip()) for i in buttons]
    except Exception as err:
        print(err)
        await msg.answer('Вы ввели данные не в том формате, пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['keyboard'] = keyboard
    await dialog_manager.switch_to(adminSG.confirm_mail)


async def cancel_malling(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.start)


async def start_malling(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    bot: Bot = dialog_manager.middleware_data.get('bot')
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get('scheduler')
    time = dialog_manager.dialog_data.get('time')
    keyboard = dialog_manager.dialog_data.get('keyboard')
    if keyboard:
        keyboard = [InlineKeyboardButton(text=i[0], url=i[1]) for i in keyboard]
    users = await session.get_users()
    if not time:
        if dialog_manager.dialog_data.get('text'):
            text: str = dialog_manager.dialog_data.get('text')
            for user in users:
                try:
                    await bot.send_message(
                        chat_id=user.user_id,
                        text=text.format(name=user.name),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None
                    )
                    if user.active == 0:
                        await session.set_active(user.user_id, 1)
                except Exception as err:
                    print(err)
                    await session.set_active(user.user_id, 0)
        elif dialog_manager.dialog_data.get('caption'):
            caption: str = dialog_manager.dialog_data.get('caption')
            if dialog_manager.dialog_data.get('photo'):
                for user in users:
                    try:
                        await bot.send_photo(
                            chat_id=user.user_id,
                            photo=dialog_manager.dialog_data.get('photo'),
                            caption=caption.format(name=user.name),
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None
                        )
                        if user.active == 0:
                            await session.set_active(user.user_id, 1)
                    except Exception as err:
                        print(err)
                        await session.set_active(user.user_id, 0)
            else:
                for user in users:
                    try:
                        await bot.send_video(
                            chat_id=user.user_id,
                            video=dialog_manager.dialog_data.get('video'),
                            caption=caption.format(name=user.name),
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None
                        )
                        if user.active == 0:
                            await session.set_active(user.user_id, 1)
                    except Exception as err:
                        print(err)
                        await session.set_active(user.user_id, 0)
    else:
        date = datetime.datetime.strptime(time, '%H:%M %d.%m')
        date = date.replace(year=datetime.datetime.today().year)
        print(type(date), date)
        scheduler.add_job(
            func=send_messages,
            args=[bot, session, InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None],
            kwargs={
                'text': dialog_manager.dialog_data.get('text'),
                'caption': dialog_manager.dialog_data.get('caption'),
                'photo': dialog_manager.dialog_data.get('photo'),
                'video': dialog_manager.dialog_data.get('video')
            },
            next_run_time=date
        )
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.start)

