"""
Файл, описывающий класс для учёта ежеминутного количества сообщений, отправляемых всеми пользователями
"""

from logging import config, getLogger

from handlers import MailHandler

config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())


class To_update():
    """
    Класс для учёта количества сообщений, отправленных пользователями в течении минутыы
    """

    def __table(self):
        # Асинхронная функция, хранящая словарь, где ключ - id пользователя, значение - количество отправленных им сообщений
        users = {}
        while True:
            query = yield
            if query[0] == 'add':
                users[query[1]] = users.get(query[1], 0) + 1
            elif query[0] == 'get':
                yield users
                users = {}
    
    def __init__(self):
        self.__data = self.__table()
        self.__data.send(None)
        logger.debug('to_update initialized')


    def add(self, user: int):
        """
        Инкрементирует количество сообщений, отправленных пользователем
        
        Аргументы:
            user: int - айди пользователя
        """
        return self.__data.send(('add', user))
    
    def get(self):
        """
        Метод для получения словаря всех пользователей, отправивших сообщения в течение минуты

        Возвращает:
            Dict[user_id: int, messages: int] - user_id - айди пользователя, messages - количество отправленных сообщений
        """
        r = self.__data.send(('get', ))
        self.__data.send(None)
        return r
