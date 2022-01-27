from discord.ext.commands import errors

class NotEnoughMoney(errors.CommandError):
    """
    The exception that is thrown
    when the user does not have enough
    funds to complete the transaction.
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class NotSelectedBetType(errors.CommandError):
    """
    The exception was thrown
    when the user does not select
    the type of bet.
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class BadGamesession(errors.CommandError):
    """
    called when the game session has expired
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class TooManyGames(errors.CommandError):
    """
    called when the game limit has been reached
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class InvalidUser(errors.CommandError):
    """
    The exception was thrown
    when the user does not selected
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)

class CommandCanceled(errors.CommandError):
    """
    The exception was thrown
    when the command gets timeout error or cancelled
    """
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message=message, *args)