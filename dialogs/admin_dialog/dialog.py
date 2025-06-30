from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url, Cancel
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.admin_dialog import getters
from states.state_groups import adminSG


admin_dialog = Dialog(
    Window(
        Const('Админ панель'),
        Column(
            Button(Const('📊 Получить статистику'), id='get_static', on_click=getters.get_static),
            SwitchTo(Const('🛫Сделать рассылку'), id='mailing_menu_switcher', state=adminSG.get_mail),
            #SwitchTo(Const('Диалоги'), id='choose_dialog_switcher', state=adminSG.choose_dialog),
            SwitchTo(Const('Отложенные сообщения'), id='queues_menu', state=adminSG.queues_menu),
            SwitchTo(Const('🔗 Управление диплинками'), id='deeplinks_menu_switcher', state=adminSG.deeplink_menu),
            SwitchTo(Const('👥 Управление админами'), id='admin_menu_switcher', state=adminSG.admin_menu),
            Button(Const('📋Выгрузка базы пользователей'), id='get_users_txt', on_click=getters.get_users_txt),
        ),
        Cancel(Const('Назад'), id='close_admin'),
        state=adminSG.start
    ),
    Window(
        Const('Здесь вы можете добавить очередь отложенных сообщений, '
              'которые будут приходить после первого старта бота пользователю\n'),
        Format('Существующие отложенные сообщения:\n{text}'),
        Column(
            SwitchTo(Const('Новая отложка'), id='add_queue_switcher', state=adminSG.add_queue),
            SwitchTo(Const('Удаление'), id='del_queues_swicher', state=adminSG.del_queue, when='queues'),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.queues_menu_getter,
        state=adminSG.queues_menu
    ),
    Window(
        Const('Нажмите на название отложенного сообщения, '
              'чтобы просмотреть его и в последствии удалить'),
        Group(
            Select(
                Format('{item[0]}'),
                id='del_queue_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_queue_selector
            ),
            width=1
        ),
        SwitchTo(Const('🔙 Назад'), id='back_queues_menu', state=adminSG.queues_menu),
        getter=getters.del_queue_getter,
        state=adminSG.del_queue
    ),
    Window(
        Const('Вы хотите удалить данное сообщение'),
        Row(
            Button(Const('Удалить'), id='del_queue', on_click=getters.del_queue),
            Button(Const('Назад'), id='back_del_queue', on_click=getters.del_queue_switcher),
        ),
        state=adminSG.confirm_del_queue
    ),
    Window(
        Const('Отправьте сообщение, которое будет рассылаться'),
        MessageInput(
            getters.get_queue_message,
            content_types=ContentType.ANY
        ),
        SwitchTo(Const('🔙 Назад'), id='back_queues_menu', state=adminSG.queues_menu),
        state=adminSG.add_queue
    ),
    Window(
        Const('Отправьте название для данного отложенного сообщения, '
              'чтобы впоследствии распознавать их среди других отложек'),
        TextInput(
            id='get_queue_name',
            on_success=getters.get_queue_name
        ),
        SwitchTo(Const('🔙 Назад'), id='back_add_queue', state=adminSG.add_queue),
        state=adminSG.get_queue_name
    ),
    Window(
        Const('Отправьте время через которое после первого запуска отправляется отправленное вами ранее сообщение'
              '\nВремя в формате: часы:минуты (н-р: 2:30)'),
        TextInput(
            id='get_queue_time',
            on_success=getters.get_queue_time
        ),
        SwitchTo(Const('🔙 Назад'), id='back_get_queue_name', state=adminSG.get_queue_name),
        state=adminSG.get_queue_time
    ),
    Window(
        Format('{text}'),
        Group(
            Select(
                Format('{item[0]}'),
                id='choose_dialog_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.dialog_selector
            ),
            width=1
        ),
        SwitchTo(Const('🔍Найти по ID или Юзернейму'), id='get_dialog_data_switcher', state=adminSG.get_dialog_data),
        Row(
            Button(Const('◀️'), id='previous_page', on_click=getters.dialog_pager, when='not_first'),
            Button(Format('{pages}'), id='pager'),
            Button(Const('▶️'), id='next_page', on_click=getters.dialog_pager, when='not_last'),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.choose_dialog_getter,
        state=adminSG.choose_dialog
    ),
    Window(
        Const('Введите user id или юзернейм пользователя с которым вы хотели бы продолжить диалог'),
        TextInput(
            id='get_user_id_username',
            on_success=getters.search_dialog
        ),
        SwitchTo(Const('🔙 Назад'), id='back_choose_dialog', state=adminSG.choose_dialog),
        state=adminSG.get_dialog_data
    ),
    Window(
        Const('Отправьте любое сообщение, оно будет доставлено пользователю'),
        MessageInput(
            func=getters.get_context_message,
            content_types=ContentType.ANY
        ),
        Button(Const('Закрыть диалог'), id='close_dialog', on_click=getters.close_dialog),
        state=adminSG.active_context
    ),
    Window(
        Format('🔗 *Меню управления диплинками*\n\n'
               '🎯 *Имеющиеся диплинки*:\n{links}'),
        Column(
            Button(Const('➕ Добавить диплинк'), id='add_deeplink', on_click=getters.add_deeplink),
            SwitchTo(Const('❌ Удалить диплинки'), id='del_deeplinks', state=adminSG.deeplink_del),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.deeplink_menu_getter,
        state=adminSG.deeplink_menu
    ),
    Window(
        Const('❌ Выберите диплинк для удаления'),
        Group(
            Select(
                Format('🔗 {item[0]}'),
                id='deeplink_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_deeplink
            ),
            width=1
        ),
        SwitchTo(Const('🔙 Назад'), id='deeplinks_back', state=adminSG.deeplink_menu),
        getter=getters.del_deeplink_getter,
        state=adminSG.deeplink_del
    ),
    Window(
        Format('👥 *Меню управления администраторами*\n\n {admins}'),
        Column(
            SwitchTo(Const('➕ Добавить админа'), id='add_admin_switcher', state=adminSG.admin_add),
            SwitchTo(Const('❌ Удалить админа'), id='del_admin_switcher', state=adminSG.admin_del)
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.admin_menu_getter,
        state=adminSG.admin_menu
    ),
    Window(
        Const('👤 Выберите пользователя, которого хотите сделать админом\n'
              '⚠️ Ссылка одноразовая и предназначена для добавления только одного админа'),
        Column(
            Url(Const('🔗 Добавить админа (ссылка)'), id='add_admin',
                url=Format('http://t.me/share/url?url=https://t.me/bot?start={id}')),  # поменять ссылку
            Button(Const('🔄 Создать новую ссылку'), id='new_link_create', on_click=getters.refresh_url),
            SwitchTo(Const('🔙 Назад'), id='back_admin_menu', state=adminSG.admin_menu)
        ),
        getter=getters.admin_add_getter,
        state=adminSG.admin_add
    ),
    Window(
        Const('❌ Выберите админа для удаления'),
        Group(
            Select(
                Format('👤 {item[0]}'),
                id='admin_del_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_admin
            ),
            width=1
        ),
        SwitchTo(Const('🔙 Назад'), id='back_admin_menu', state=adminSG.admin_menu),
        getter=getters.admin_del_getter,
        state=adminSG.admin_del
    ),
    Window(
        Const('Введите сообщение которое вы хотели бы разослать\n\n<b>Предлагаемый макросы</b>:'
              '\n{name} - <em>полное имя пользователя</em>'),
        MessageInput(
            content_types=ContentType.ANY,
            func=getters.get_mail
        ),
        SwitchTo(Const('Назад'), id='back', state=adminSG.start),
        state=adminSG.get_mail
    ),
    Window(
        Const('Введите дату и время в которое сообщение должно отправиться всем юзерам в формате '
              'час:минута:день:месяц\n Например: 18:00 10.02 (18:00 10-ое февраля)'),
        TextInput(
            id='get_time',
            on_success=getters.get_time
        ),
        SwitchTo(Const('Продолжить без отложки'), id='get_keyboard_switcher', state=adminSG.get_keyboard),
        SwitchTo(Const('Назад'), id='back_get_mail', state=adminSG.get_mail),
        state=adminSG.get_time
    ),
    Window(
        Const('Введите кнопки которые будут крепиться к рассылаемому сообщению\n'
              'Введите кнопки в формате:\n кнопка1 - ссылка1\nкнопка2 - ссылка2'),
        TextInput(
            id='get_mail_keyboard',
            on_success=getters.get_mail_keyboard
        ),
        SwitchTo(Const('Продолжить без кнопок'), id='confirm_mail_switcher', state=adminSG.confirm_mail),
        SwitchTo(Const('Назад'), id='back_get_time', state=adminSG.get_time),
        state=adminSG.get_keyboard
    ),
    Window(
        Const('Вы подтверждаете рассылку сообщения'),
        Row(
            Button(Const('Да'), id='start_malling', on_click=getters.start_malling),
            Button(Const('Нет'), id='cancel_malling', on_click=getters.cancel_malling),
        ),
        SwitchTo(Const('Назад'), id='back_get_keyboard', state=adminSG.get_keyboard),
        state=adminSG.confirm_mail
    ),
)