import datetime

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode, ShowMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from keyboards.keyboard import get_open_context_keyboard
from utils.schedulers import start_queue, custom_queue
from utils.build_ids import get_random_id
from database.action_data_class import DataInteraction
from config_data.config import Config, load_config
from states.state_groups import adminSG


config: Config = load_config()


user_router = Router()


@user_router.message(CommandStart())
async def start_dialog(msg: Message, dialog_manager: DialogManager, session: DataInteraction, command: CommandObject, scheduler: AsyncIOScheduler):
    args = command.args
    #referral = None
    if args:
        link_ids = await session.get_links()
        ids = [i.link for i in link_ids]
        if args in ids:
            await session.add_admin(msg.from_user.id, msg.from_user.full_name)
            await session.del_link(args)
        if not await session.check_user(msg.from_user.id):
            deeplinks = await session.get_deeplinks()
            deep_list = [i.link for i in deeplinks]
            if args in deep_list:
                await session.add_entry(args)
            #try:
                #args = int(args)
                #users = [user.user_id for user in await session.get_users()]
                #if args in users:
                    #referral = args
                    #await session.add_refs(args)
            #except Exception as err:
                #print(err)
    admins = config.bot.admin_ids
    admins.extend([admin.user_id for admin in await session.get_admins()])
    keyboard = await get_open_context_keyboard(msg.from_user.id)
    if not await session.check_user(msg.from_user.id):
        await session.add_user(msg.from_user.id, msg.from_user.username if msg.from_user.username else 'Отсутствует',
                               msg.from_user.full_name)
        #scheduler.add_job(
            #start_queue,
            #'interval',
            #args=[msg.from_user.id, msg.bot, session, scheduler],
            #id=f'{msg.from_user.id}_queue'
        #)
        queues = await session.get_queues()
        for queue in queues:
            date = datetime.datetime.today() + datetime.timedelta(hours=queue.minutes // 60, minutes=queue.minutes % 60)
            job_id = f'{get_random_id()}_{msg.from_user.id}'
            scheduler.add_job(
                custom_queue,
                args=[msg.bot, msg.from_user.id, queue.message_id, queue.chat_id, session],
                next_run_time=date,
                id=job_id
            )
        """
        await session.add_dialog_message(msg.from_user.id, msg.message_id, 'user')
        user = await session.get_user(msg.from_user.id)
        text = f'❗<b>Пользователь c ID {user.user_id} (@{user.username}) впервые запустил бота</b>'
        for admin in admins:
            await msg.bot.send_message(
                chat_id=admin,
                text=text,
                reply_markup=keyboard
            )
    else:
        contexts = await session.get_user_contexts(msg.from_user.id)
        if not contexts:
            await session.add_dialog_message(msg.from_user.id, msg.message_id, 'user')
            user = await session.get_user(msg.from_user.id)
            text = f'❗<b>Пользователь c ID {user.user_id} (@{user.username}) повторно запустил бота</b>'
            for admin in admins:
                await msg.bot.send_message(
                    chat_id=admin,
                    text=text,
                    reply_markup=keyboard
                )
        else:
            await session.add_dialog_message(msg.from_user.id, msg.message_id, 'user', read=True)
            for context in contexts:
                warning_message = await msg.bot.send_message(
                    chat_id=context.admin_id,
                    text='<b>Сообщение от пользователя:</b>'
                )
                message = await msg.bot.copy_message(
                    chat_id=context.admin_id,
                    from_chat_id=msg.from_user.id,
                    message_id=msg.from_user.id
                )
                await session.add_context_message_ids(
                    msg.from_user.id,
                    context.admin_id,
                    [warning_message.message_id, message.message_id]
                )
        """

    if msg.from_user.id in admins:
        await dialog_manager.start(state=adminSG.start, mode=StartMode.RESET_STACK)


@user_router.message()
async def get_message(msg: Message, scheduler: AsyncIOScheduler):
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id.endswith(str(msg.from_user.id)):
            job.remove()


"""
@user_router.message()
async def get_message(msg: Message, dialog_manager: DialogManager, session: DataInteraction):
    contexts = await session.get_user_contexts(msg.from_user.id)
    if contexts:
        await session.add_dialog_message(msg.from_user.id, msg.message_id, 'user', read=True)
        for context in contexts:
            warning_message = await msg.bot.send_message(
                chat_id=context.admin_id,
                text='<b>Сообщение от пользователя:</b>'
            )
            message = await msg.bot.copy_message(
                chat_id=context.admin_id,
                from_chat_id=msg.from_user.id,
                message_id=msg.message_id
            )
            await session.add_context_message_ids(
                msg.from_user.id,
                context.admin_id,
                [warning_message.message_id, message.message_id]
            )
    else:
        await session.add_dialog_message(msg.from_user.id, msg.message_id, 'user')
        admins = config.bot.admin_ids
        admins.extend([admin.user_id for admin in await session.get_admins()])
        user = await session.get_user(msg.from_user.id)
        text = f'❗<b>Пользователь c ID {user.user_id} (@{user.username}) отправил вам сообщение</b>'
        keyboard = await get_open_context_keyboard(msg.from_user.id)
        for admin in admins:
            await msg.bot.send_message(
                chat_id=admin,
                text=text,
                reply_markup=keyboard
            )
"""
