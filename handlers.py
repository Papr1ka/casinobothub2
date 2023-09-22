"""
Файл с инструментами для логгинга
"""

from logging.handlers import SMTPHandler
from logging import ERROR
from logging import Formatter
from os import environ

from .settings import MAIL_PASS, MAIL_LOGIN

class simpleFormatter(Formatter):
    """
    Простой форматтер лога, используется во всех обработчиках
    """
    __fmt = "%(name)s : %(funcName)s : %(lineno)d : %(asctime)s : %(levelname)s : %(message)s"
    __datefmt = "%d/%m/%Y %I:%M:%S %p"

    def __init__(self):
        super().__init__(fmt=simpleFormatter.__fmt, datefmt=simpleFormatter.__datefmt)

class MailHandler(SMTPHandler):
    """
    Обработчик логов с возможностью отправки на почту, в logging.ini указан порог срабатывания - CRITICAL
    """
    # Хост
    __mailhost = ('smtp.gmail.com', 587) 
    # От кого
    __fromaddr = MAIL_LOGIN
    # Кому
    __toaddrs = __fromaddr
    # Тема сообжения
    __subject = "Log Record"
    # Данные для авторизации
    __credentials = (__fromaddr, MAIL_PASS)
    __secure = ()
    def __init__(self):
        super().__init__(mailhost=MailHandler.__mailhost,
                        fromaddr=MailHandler.__fromaddr,
                        toaddrs=MailHandler.__toaddrs,
                        subject=MailHandler.__subject,
                        credentials=MailHandler.__credentials,
                        secure=MailHandler.__secure)
        self.setLevel(ERROR)
        self.formatter = simpleFormatter()
    
    def getSubject(self, record):
        return f"{self.subject}: {record.levelname}"
