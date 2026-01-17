from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    )


main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕ Реєстрація"), KeyboardButton(text="🔑 Вхід")],
], resize_keyboard=True)



account_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="❌ Видалити рахунок")],
        [KeyboardButton(text="➕ Поповнити"), KeyboardButton(text="➖ Зняти"), KeyboardButton(text="➕ Поповнити (рандомне: 1-100)")],
        [KeyboardButton(text="🔁 Переказ")],
        [KeyboardButton(text="📜 Історія"),KeyboardButton(text="🚪 Вийти")],
        
    ],
    resize_keyboard=True
)