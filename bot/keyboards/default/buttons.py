from aiogram.types import ReplyKeyboardMarkup , KeyboardButton
from data.config import WEB_URL
menu  = ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text="Xaridni boshlash 🛍",web_app={"url":f"https://{WEB_URL}"})   
        ],   
        [
            KeyboardButton(text="🌍 Do‘kon manzili"),
            KeyboardButton(text="📲 Kontaktlar"),
        ]  
    ]
)