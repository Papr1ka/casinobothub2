"""
Файл описывает кастомные ошибки бота, связанные с действиями пользователей
"""

from discord.ext.commands import errors

class NotEnoughMoney(errors.CommandError):
    """
    Выбрасывается, когда у пользователя недостаточно денег для совершения операции
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class NotSelectedBetType(errors.CommandError):
    """
    Выбрасывается, когда пользователь не выбрал тип ставки в казино
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class BadGamesession(errors.CommandError):
    """
    Выбрасывается, когда пользователь обращается к устаревшей сессии в казино
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class TooManyGames(errors.CommandError):
    """
    Выбрасывается, когда пользователь превышает лимит одновременных игр
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class InvalidUser(errors.CommandError):
    """
    Выбрасывается, когда пользователь не выбран
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class CommandCanceled(errors.CommandError):
    """
    Выбрасывается, когда время действия команды истекло или команда была отменена
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)
