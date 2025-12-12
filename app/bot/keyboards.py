from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


kb_contact = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Send Contact", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

kb_vacancies = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐍 Python Backend Developer")],
        [KeyboardButton(text="🔙 To the Beginning")],
    ],
    resize_keyboard=True,
)

kb_cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔙 Cancel")]], resize_keyboard=True
)
