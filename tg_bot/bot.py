"""Главный модуль"""

from extensions import TgBot

Bot = TgBot()

while True:
    try:
        Bot.bot.polling()
    except Exception:
        continue

