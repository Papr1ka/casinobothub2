from handlers import MailHandler
from logging import config, getLogger

config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())


class To_update():

    def __table(self):
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


    def add(self, user):
        return self.__data.send(('add', user))
    
    def get(self):
        r = self.__data.send(('get', ))
        self.__data.send(None)
        return r
