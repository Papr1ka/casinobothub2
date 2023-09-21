from os import environ
from dotenv import load_dotenv
from logging import config, getLogger

config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)

load_dotenv()

# Токен бота discord
TOKEN = environ.get("TOKEN")
# Имя базы данных
DATABASE_NAME = environ.get("DATABASE_NAME")
# Имя базы данных по умолчанию
DEFAULT_DATABASE_NAME = "casino_shared"
# Пароль базы данных
MONGO_PASSWORD = environ.get("MONGO_PASSWORD")
# Токен для авторизации на сайте top.gg (для проверки, голосовал ли пользователь за бота)
DBL_TOKEN = environ.get("DBL_TOKEN")

# см. использование в database.py
THREAD_SIZE = 30

# см. использование в database.py
SHARD_COUNT = 100

# Шаблон формирования строки для подключения к базе данных
# Старый вид, использовался для подключения к облаку
# DATABASE_URL_PATTERN = "mongodb+srv://user:%s@cluster0.qbwbb.mongodb.net/%s?retryWrites=true&w=majority"
DATABASE_URL_PATTERN = "mongodb://localhost:27017/default?ssl=false&replicaSet=rs0&readPreference=primary"
# Должна быть уже отформатированна, т.е. DATABASE_URL_STRING = DATABASE_URL_PATTERN % (DATABASE_NAME, DATABASE_PASSWORD)
DATABASE_URL_STRING = DATABASE_URL_PATTERN

# Количество шардов бота
SHARD_COUNT=1

logger.info("ENV loaded")
if TOKEN == "": logger.debug("TOKEN is empty")
if MONGO_PASSWORD == "": logger.debug("MONGO_PASSWORD is empty")
if DBL_TOKEN == "": logger.debug("DBL_TOKEN is empty")
if DATABASE_NAME == "":
    logger.debug("DATABASE_NAME is empty, using default")
    DATABASE_NAME = DEFAULT_DATABASE_NAME
