from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    selecting_language = State()
    main_menu = State()
    selecting_style = State()
    uploading_photo = State()
    selecting_package = State()
    uploading_payment = State()
