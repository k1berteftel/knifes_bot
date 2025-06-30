import asyncio
from aiogram import Bot
from aiogram import Bot
from aiogram_dialog import DialogManager
from aiogram.types import InlineKeyboardMarkup, Message, FSInputFile
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.action_data_class import DataInteraction


async def send_messages(bot: Bot, session: DataInteraction, keyboard: InlineKeyboardMarkup | None, **kwargs):
    users = await session.get_users()
    text = kwargs.get('text')
    caption = kwargs.get('caption')
    photo = kwargs.get('photo')
    video = kwargs.get('video')
    if text:
        for user in users:
            try:
                await bot.send_message(
                    chat_id=user.user_id,
                    text=text.format(name=user.name),
                    reply_markup=keyboard
                )
                if user.active == 0:
                    await session.set_active(user.user_id, 1)
            except Exception as err:
                print(err)
                await session.set_active(user.user_id, 0)
    elif caption:
        if photo:
            for user in users:
                try:
                    await bot.send_photo(
                        chat_id=user.user_id,
                        photo=photo,
                        caption=caption.format(name=user.name),
                        reply_markup=keyboard
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
                        video=video,
                        caption=caption.format(name=user.name),
                        reply_markup=keyboard
                    )
                    if user.active == 0:
                        await session.set_active(user.user_id, 1)
                except Exception as err:
                    print(err)
                    await session.set_active(user.user_id, 0)


async def start_queue(user_id: int, bot: Bot, session: DataInteraction, scheduler: AsyncIOScheduler):
    text = ('Здравия, меня зовут Михаил - я кузнец! \nКак раз клинок заканчиваю для своей финки - посмотрите.\n\n'
            'При заказе сегодня Доставка в ПОДАРОК!\n\nРасскажите, Вы под какие задачи нож подбираете ? '
            '( это нужно чтобы сталь подобрать)')
    message = await bot.send_message(
        chat_id=user_id,
        text=text
    )
    #await session.add_dialog_message(user_id, message.message_id, 'me')
    await asyncio.sleep(10)
    try:
        message = await bot.send_video_note(
            chat_id=user_id,
            video_note=FSInputFile(path='media/start_note.mp4'),
            request_timeout=60
        )
        #await session.add_dialog_message(user_id, message.message_id, 'me')
    except Exception as err:
        print(err)
    text = ('Сегодня от души кладу подарок к заказу\nПод какие задачи нож смотрите? Охота, рыбалка, '
            'в походы или на кухню? Подберу подходящий🔘')
    await asyncio.sleep(30)
    message = await bot.send_message(
        chat_id=user_id,
        text=text
    )
    #await session.add_dialog_message(user_id, message.message_id, 'me')
    job = scheduler.get_job(f'{user_id}_queue')
    if job:
        job.remove()


async def custom_queue(bot: Bot, user_id: int, message_id: int, chat_id: int, session: DataInteraction):
    try:
        await bot.copy_message(
            chat_id=user_id,
            message_id=message_id,
            from_chat_id=chat_id,
            request_timeout=60
        )
    except Exception as err:
        print(err)
        await session.set_active(user_id, 0)

