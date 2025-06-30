import datetime
from typing import Literal

from sqlalchemy import select, insert, update, column, text, delete, and_, desc

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.model import (UsersTable, DeeplinksTable, OneTimeLinksIdsTable, AdminsTable, QueuesTable)  # , DialogsTable, ContextsTable)


class DataInteraction():
    def __init__(self, session: async_sessionmaker):
        self._sessions = session

    async def check_user(self, user_id: int) -> bool:
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.user_id == user_id))
        return True if result else False

    async def add_user(self, user_id: int, username: str, name: str):
        if await self.check_user(user_id):
            return
        async with self._sessions() as session:
            await session.execute(insert(UsersTable).values(
                user_id=user_id,
                username=username,
                name=name,
            ))
            await session.commit()

    async def add_queue(self, name: str, message_id: int, chat_id: int, minutes: int):
        async with self._sessions() as session:
            await session.execute(insert(QueuesTable).values(
                name=name,
                message_id=message_id,
                chat_id=chat_id,
                minutes=minutes
            ))
            await session.commit()

    """

    async def add_dialog_message(self, user_id: int, message_id: int, sender: Literal['me', 'user'], read: bool = False):
        dialogs = await self.get_dialog(user_id)
        if len(dialogs) >= 10:
            count = len(dialogs) - 10
            await self.del_last_message(user_id, count)
        async with self._sessions() as session:
            await session.execute(insert(DialogsTable).values(
                user_id=user_id,
                message_id=message_id,
                sender=sender,
                read=read
            ))
            await session.commit()

    async def add_context_message_ids(self, user_id: int, admin_id: int, message_ids: list):
        async with self._sessions() as session:
            context = await session.scalar(select(ContextsTable).where(and_(
                ContextsTable.user_id == user_id,
                ContextsTable.admin_id == admin_id
            )))
            context.message_ids = context.message_ids + message_ids
            await session.commit()

    async def add_context(self, admin_id: int, user_id: int, message_ids: list):
        async with self._sessions() as session:
            await session.execute(insert(ContextsTable).values(
                admin_id=admin_id,
                user_id=user_id,
                message_ids=message_ids
            ))
            await session.commit()
    """

    async def add_entry(self, link: str):
        async with self._sessions() as session:
            await session.execute(update(DeeplinksTable).where(DeeplinksTable.link == link).values(
                entry=DeeplinksTable.entry+1
            ))
            await session.commit()


    async def add_deeplink(self, link: str):
        async with self._sessions() as session:
            await session.execute(insert(DeeplinksTable).values(
                link=link
            ))
            await session.commit()

    async def add_link(self, link: str):
        async with self._sessions() as session:
            await session.execute(insert(OneTimeLinksIdsTable).values(
                link=link
            ))
            await session.commit()

    async def add_admin(self, user_id: int, name: str):
        async with self._sessions() as session:
            await session.execute(insert(AdminsTable).values(
                user_id=user_id,
                name=name
            ))
            await session.commit()

    async def get_users(self):
        async with self._sessions() as session:
            result = await session.scalars(select(UsersTable))
        return result.fetchall()

    async def get_user(self, user_id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.user_id == user_id))
        return result

    async def get_user_by_username(self, username: str):
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.username == username))
        return result

    async def get_queues(self):
        async with self._sessions() as session:
            result = await session.scalars(select(QueuesTable))
        return result.fetchall()

    async def get_queue(self, id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(QueuesTable).where(QueuesTable.id == id))
        return result

    """
    async def get_dialog(self, user_id: int):
        async with self._sessions() as session:
            result = await session.scalars(select(DialogsTable).where(DialogsTable.user_id == user_id).order_by(DialogsTable.date))
        return result.fetchall()

    async def get_user_contexts(self, user_id: int):
        async with self._sessions() as session:
            result = await session.scalars(select(ContextsTable).where(ContextsTable.user_id == user_id))
        return result.fetchall()

    async def get_admin_context(self, user_id: int, admin_id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(ContextsTable).where(and_(
                ContextsTable.user_id == user_id,
                ContextsTable.admin_id == admin_id
            )))
        return result
    """
    async def get_links(self):
        async with self._sessions() as session:
            result = await session.scalars(select(OneTimeLinksIdsTable))
        return result.fetchall()

    async def get_admins(self):
        async with self._sessions() as session:
            result = await session.scalars(select(AdminsTable))
        return result.fetchall()

    async def get_deeplinks(self):
        async with self._sessions() as session:
            result = await session.scalars(select(DeeplinksTable))
        return result.fetchall()

    async def set_activity(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                activity=datetime.datetime.today()
            ))
            await session.commit()

    async def set_active(self, user_id: int, active: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                active=active
            ))
            await session.commit()

    """

    async def set_read(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(update(DialogsTable).where(DialogsTable.user_id == user_id).values(
                read=True
            ))
            await session.commit()
    """

    async def del_queue(self, id: int):
        async with self._sessions() as session:
            await session.execute(delete(QueuesTable).where(QueuesTable.id == id))
            await session.commit()

    async def del_deeplink(self, link: str):
        async with self._sessions() as session:
            await session.execute(delete(DeeplinksTable).where(DeeplinksTable.link == link))
            await session.commit()

    async def del_link(self, link_id: str):
        async with self._sessions() as session:
            await session.execute(delete(OneTimeLinksIdsTable).where(OneTimeLinksIdsTable.link == link_id))
            await session.commit()


    """
    async def del_user_context(self, admin_id: int, user_id: int):
        async with self._sessions() as session:
            await session.execute(delete(ContextsTable).where(and_(
                ContextsTable.user_id == user_id,
                ContextsTable.admin_id == admin_id
            )))
            await session.commit()

    async def del_last_message(self, user_id: int, count: int):  # добавить удаление самого старого сообщения
        dialog = await self.get_dialog(user_id)
        async with self._sessions() as session:
            counter = 0
            for message in reversed(dialog):
                if counter == count:
                    break
                await session.execute(delete(DialogsTable).where(DialogsTable.id == message.id))
                counter += 1
            await session.commit()
    """
    async def del_admin(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(delete(AdminsTable).where(AdminsTable.user_id == user_id))
            await session.commit()