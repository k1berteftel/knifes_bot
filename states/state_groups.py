from aiogram.fsm.state import State, StatesGroup

# Обычная группа состояний


class adminSG(StatesGroup):
    start = State()
    get_mail = State()
    get_time = State()
    get_keyboard = State()
    confirm_mail = State()
    deeplink_menu = State()
    deeplink_del = State()
    admin_menu = State()
    admin_del = State()
    admin_add = State()
    choose_dialog = State()
    get_dialog_data = State()
    active_context = State()
    queues_menu = State()
    add_queue = State()
    get_queue_name = State()
    get_queue_time = State()
    del_queue = State()
    confirm_del_queue = State()
