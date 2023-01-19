"""Модуль для пользовательских исключений"""

class CurrencyNotFoundException(Exception):
    """Исключение, возникающее, когда определенная валюта не найдена"""
    def __init__(self, base: str, quote: str, currency: str):
        super().__init__(f"Валюта {currency} не найдена для базы {base} и котировки {quote}") # допилить
        self.base = base
        self.quote = quote
        self.currency = currency


class AmountNotFoundException(Exception):
    """Исключение, возникающее, когда сумма не найдена"""
    def __init__(self):
        super().__init__("Сумма не найдена")


class CBRException(Exception):
    """Исключение, вызванное CBR"""
    def __init__(self, message: str):
        super().__init__(message)


class BadMessageFormatException(Exception):
    """Исключение, возникающее, когда сообщение имеет неправильный формат"""
    def __init__(self, message: str):
        super().__init__(message)
