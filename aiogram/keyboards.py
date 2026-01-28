from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    )


before_loggin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕ Реєстрація"), KeyboardButton(text="🔑 Вхід")],
], resize_keyboard=True)



after_loggin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="❌ Видалити рахунок")],
        [KeyboardButton(text="➕ Поповнити"), KeyboardButton(text="➖ Зняти"), KeyboardButton(text="➕ Поповнити (рандомне: 1-100)")],
        [KeyboardButton(text="🔁 Переказ")],
        [KeyboardButton(text="📜 Історія"),KeyboardButton(text="🚪 Вийти")],
        
    ],
    resize_keyboard=True
)


currency_inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 USD", callback_data="currency_USD"),
            InlineKeyboardButton(text="💶 EUR", callback_data="currency_EUR"),
            InlineKeyboardButton(text="💴 UAH", callback_data="currency_UAH"),
        ]
    ]
)