from logging.handlers import SMTPHandler
from logging import ERROR
from logging import Formatter
from os import environ

class simpleFormatter(Formatter):
    __fmt = "%(name)s : %(funcName)s : %(lineno)d : %(asctime)s : %(levelname)s : %(message)s"
    __datefmt = "%d/%m/%Y %I:%M:%S %p"

    def __init__(self):
        super().__init__(fmt=simpleFormatter.__fmt, datefmt=simpleFormatter.__datefmt)

class MailHandler(SMTPHandler):
    __mailhost = ('smtp.gmail.com', 587) 
    __fromaddr = environ.get('maillogin')
    __toaddrs = __fromaddr
    __subject = "Log Record"
    __credentials = (__fromaddr, environ.get('mailpass'))
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