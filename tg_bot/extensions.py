"""Модуль реализующий класс бота и его функции"""

from typing import Dict, Tuple
from requests import get
from telebot import TeleBot, types
from config import BOT_TOKEN
import errors

class TgBot():
    """Этот класс представляет Telegram Bot, позволяющий общаться
    с пользователями Telegram через Telegram API"""
    bot: TeleBot
    chat_handler: dict
    chat_states = {'started':0, 'entered':1}

    def __init__(self) -> None:
        self.bot = TeleBot(BOT_TOKEN)
        self.bot.message_handler(commands=['start'])(self.start)
        self.bot.message_handler(commands=['help'])(self.help)
        self.bot.message_handler(commands=['values'])(self.values)
        self.bot.message_handler(content_types=['text'])(self.func)
        self.bot.remove_webhook()

        self.chat_handler = dict()


    @staticmethod
    def create_keyboard(*args: str) -> types.ReplyKeyboardMarkup:
        """Дополнительная функция для удобного создания кнопок"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        # Создаем кнопки
        buttons = []
        for button in args:
            buttons.append(types.KeyboardButton(button))

        # Добавляем их в разметку
        markup.add(*buttons)

        return markup


    def start(self, message: types.Message) -> None:
        """Обработка команды /start"""

        markup = TgBot().create_keyboard('👋 Начать', '❓ Помощь')

        # Отправляем приветсвие
        self.bot.send_message(message.chat.id, \
            f"Привет, {message.from_user.first_name}. Это бот-конвертер валют. Выбери опцию:", reply_markup=markup)

        self.chat_handler[message.chat.id] = self.chat_states['started']


    def help(self, message: types.Message) -> None:
        """Команда help"""

        help_message = """I am a simple Telegram
            bot that can respond to the /start and /help commands."""

        self.bot.send_message(message.chat.id, help_message)


    def values(self, message: types.Message) -> None:
        """Команда values"""

        values_message = ""

        nom_dict = TgBot.set_dict()
        
        for nom in nom_dict:
            values_message += f'\n- {nom} - {nom_dict[nom][0]}'

        self.bot.send_message(message.chat.id, values_message)


    def func(self, message: types.Message) -> None:
        """Обработка команд"""
        chat_id = message.chat.id

        if(message.text == "👋 Начать"):
            markup = TgBot().create_keyboard('❓ Помощь')

            self.bot.send_message(chat_id, text="Введите запрос или воспользуйтесь кнопкой 'Помощь' для получения дополнительной информации", reply_markup=markup)

            self.chat_handler[chat_id] = self.chat_states['entered']


        elif(message.text == "❓ Помощь"):
            markup = TgBot().create_keyboard('❓ Как работает бот?', 
                                             'Валюты',
                                             'Вернуться в главное меню')

            self.bot.send_message(chat_id, text="Чем могу помочь?", reply_markup=markup)
        
        
        elif(message.text == 'Валюты'):
            self.values(message)


        elif(message.text == "❓ Как работает бот?"):
            self.bot.send_message(chat_id, "Бот возвращает цену на определённое количество валюты.\n"
                                            "Отправьте сообщение боту одной строкой, вводя через пробел:\n"
                                            "короткое имя валюты, цену которой хотите узнать,\n"
                                            "короткое имя валюты, в которой надо узнать цену первой валюты,\n"
                                            "количество первой валюты")


        elif (message.text == "Вернуться в главное меню"):
            if self.chat_states['started'] == self.chat_handler[chat_id]:
                markup = TgBot().create_keyboard('👋 Начать', '❓ Помощь')

            elif self.chat_states['entered'] == self.chat_handler[chat_id]:
                markup = TgBot().create_keyboard('❓ Помощь')

            self.bot.send_message(chat_id, text="Вы вернулись в главное меню", reply_markup=markup)


        else:
            if self.chat_states['started'] == self.chat_handler[chat_id]:
                self.bot.send_message(chat_id, text="На такую комманду я не запрограммирован..")

            elif self.chat_states['entered'] == self.chat_handler[chat_id]:
                text = message.text
                try:
                    base, quote, amount = TgBot().get_base_quote_amount(chat_id, text)

                    if None in (base, quote, amount):
                        return

                    if base not in TgBot().set_dict():
                        raise errors.CurrencyNotFoundException(base, quote, currency=base)
                    elif quote not in TgBot().set_dict():
                        raise errors.CurrencyNotFoundException(base, quote, currency=quote)

                except errors.CurrencyNotFoundException as e:
                    self.bot.send_message(chat_id, f'Currency {e.currency} is not found.')
                    return

                try:
                    base, quote, amount = TgBot().get_base_quote_amount(chat_id, text)
                except e:
                    return

                resp_msg = TgBot().get_price(base, quote, amount)

                self.bot.send_message(chat_id, resp_msg)


    @staticmethod
    def set_dict() -> Dict[str, Tuple[str, float]]:
        """
        Описание:
        ------------
            Этот метод устанавливает словарь, содержащий название, код и стоимость
            различных валют в соответствии с API Центрального банка России.

        Возвращает:
        ------------
            `Dict[str, Tuple[str, float]]` : Словарь, содержащий код валюты в
            качестве ключа и кортеж из названия и значения валюты в качестве значения.
        """
        nom_dict = dict()

        response = get('https://www.cbr-xml-daily.ru/daily_json.js', timeout=10)

        if response.status_code != 200:
            raise errors.CBRException(f'Bad status code {response.status_code}')

        body = dict(response.json()['Valute'])

        for i in body:
            nom_dict[body[i]['CharCode']] = \
                tuple([body[i]['Name'], body[i]['Value'] / body[i]['Nominal']])

        nom_dict['RUB'] = tuple(['Российский рубль', 0])

        return nom_dict


    @staticmethod
    def get_price(base: str, quote: str, amount: float) -> str:
        """
        Описание:
        ------------
            Функция использует словарь для получения курса конвертации между базовой и котируемой
            валютами и выполняет конвертацию. Если базовая или котируемая валюта - RUB (российский
            рубль), то в возвращаемую строку будет включено слово "Рублей".

        Аргументы:
        ------------
            `base` : `str`, представляющая базовую валюту
            `quote` : `str`, представляющая валюту котировки
            `amount` : `float`, представляющая сумму базовой валюты.

        Аргументы:
        ------------
            Функция возвращает строку в формате
            "сумма_базовая_валюта = значение_котировочной_валюты".
        """
        nom_dict = TgBot().set_dict()

        if quote == 'RUB':
            value = round(amount * nom_dict[base][1], 2)

            return str(amount) + " " + str(nom_dict[base][0]) + " = " + str(value) + " " + "Рублей"

        elif base == 'RUB':
            value = round(amount * 1 / nom_dict[quote][1], 2)

            return str(amount) + " " + 'Рублей' + " = " + str(value) + " " \
                + str(nom_dict[quote][0])

        else:
            value = round(amount * nom_dict[base][1] / nom_dict[quote][1], 2)

            return str(amount) + " " + str(nom_dict[base][0]) + " = " + str(value) \
                + " " + str(nom_dict[quote][0])


    def get_base_quote_amount(self, chat_id: int, message: str) -> Tuple[str, str, float]:
        """
        Описание:
        ------------
            Эта функция принимает на вход идентификатор чата и сообщение. Она разбивает
            сообщение на список и пытается извлечь из него базовую валюту, валюту котировки и сумму.

            Если извлечение прошло успешно, она возвращает базовую валюту, валюту котировки и сумму
            в виде кортежа.

            Если извлечение не удалось, он посылает сообщение об ошибке на chat_id и возвращает None
            для базовой валюты, валюты котировки и суммы.
        """
        my_list = message.upper().split()

        try:
            base = my_list[0].strip()
            quote = my_list[1].strip()

            try:
                amount = float(my_list[2].strip())
                return base, quote, amount

            except ValueError:
                self.bot.send_message(chat_id, 'Amount have wrong format')
                return base, quote, None

        except IndexError:
            self.bot.send_message(chat_id, 'Wrong format of message')
            return None, None, None
