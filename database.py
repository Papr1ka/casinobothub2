"""
Файл с единственным клиентом для работы с базой банных mongodb
"""

from aiohttp import ClientSession as aioSession
from asyncio import get_event_loop, create_task, gather, coroutine
from logging import config, getLogger
from motor.motor_asyncio import AsyncIOMotorClient
from math import ceil
from time import time

from handlers import MailHandler
from models.user_model import UserModel
from models.shop import get_shop
from settings import MONGO_PASSWORD, DBL_TOKEN, DATABASE_URL_STRING, DATABASE_NAME, THREAD_SIZE, SHARD_COUNT

config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())



class Database(AsyncIOMotorClient):
    """
    Класс для работы с базой данных
    """
    # Имя базы данных
    __database_name = DATABASE_NAME
    # Пароль базы данных
    __mongo_password = MONGO_PASSWORD

    """
    Количество запросов для запуска 1-й транзакции
    Одновременно на множестве серверов множество людей пишет сообщения,
    если обновлять статистику опыта и количества сообщений для пользователя на каждое сообщение, то получится слишком много запросов в секунду,
    поэтому было сделано некоторое изощрение
    каждую минуту запускается n асинхронных транзакций, каждая из которых выполняет до THREAD_SIZE запросов в базу данных
    запросов также много, но работает всё быстрее, в будущем требуется оптимизировать или переработать этот вопрос
    см. Database.update_many, Database.update_thread
    """
    __thread_size = THREAD_SIZE
    # Токен для работы с сервисом top.gg
    __dbl_token = DBL_TOKEN
    # Адрес сервиса top.gg
    __site_url = "https://top.gg/api"

    """
    Количество шардов в базе данных
    В облаке, возможно было ограничение на размер одной коллекции в рамках базы данных, возможно я неправ
    Поиск в рамках одной коллекции при экстремально больших объёмах будет дольше, чем в 2-х вдвое меньших
    В текущей реализации все обрабатываемые ботом сервера разделяются на разные коллекции mongo
    Shard_count - это количество коллекций
    Номер шарда (коллекции) из [0, SHARD_COUNT]
    вычисляется в get_shard (guild_id >> 22 % SHARD_COUNT)
    При работе с базой данных обращение к шардам автоматическое, об этом беспокоиться не нужно
    Другой вопрос - практическая польза от этого. Полагаю, при 100 шардах запас огромный, но нужно глубже разбираться в mongodb
    """
    __shard_count = SHARD_COUNT

    def __init__(self):
        pass

    def timeit(func: coroutine):
        """
        Отладочный декоратор для измерения времени выполнения запроса в базу данных
        
        Аргументы:
            func: asyncio.coroutine - оборачиваемая корутина
        """
        async def wrapper(self, *args, **kwargs):
            t0 = time()
            result = await func(self, *args, **kwargs)
            t1 = time()
            logger.debug(f'{func.__name__} done, time: {t1-t0}s')
            return result
        return wrapper
    
    def connect(self, database_name: str=None):
        """
        Метод подключения к базе данных

        Аргументы:
            database_name: str - имя базы данных, если None, используется имя из файла settings.py
        """
        logger.debug('connecting to cluster...')
        if database_name is not None:
            self.__database_name = database_name
        try:
            # Подключение
            super().__init__(DATABASE_URL_STRING)

            logger.debug(self.server_info())
            self.db = self[self.__database_name]

            # Определение функции получения событийного цикла, необходимо, чтобы присоединить работу базы данных к основному циклу
            self.get_io_loop = get_event_loop
        except Exception as E:
            logger.critical(f"can't connect to database: {E}")
        else:
            logger.info(f"connected to database: {self.__database_name}")

    def Correct_ids(function: coroutine):
        """
        Декоратор для проверки айди гильдии и пользователя на корректность, чтобы избежать непредвиденного повидения в базе данных

        Аргументы:
            function: asyncio.coroutine - оборачиваемая корутина
        """
        async def wrapper(self, *args, **kwargs):
            guild_id = args[0]
            if await Database.__check_id(guild_id):
                user_id = args[1]
                if await Database.__check_id(user_id):
                    return await function(self, *args, **kwargs)
                logger.error(f"invalid user_id: {user_id}, {type(user_id)}, int required")
                raise ValueError(f"invalid user_id: {user_id}, {type(user_id)}, int required")
            logger.error(f"invalid guild_id: {guild_id}, {type(guild_id)}, int required")
            raise ValueError(f"invalid guild_id: {guild_id}, {type(guild_id)}, int required")
        return wrapper

    @staticmethod
    async def __check_id(user_id):
        """
        Метод для проверки айди гильдии и пользователя на корректность

        Аргументы:
            user_id: Any - проверяемый айди
        
        Возвращает:
            True, если айди корректный, иначе False
        """
        if isinstance(user_id, int):
            return True
        else:
            return False
    
    async def get_shard(self, guild_id: int) -> str:
        """
        Метод для получения имени коллекции

        Аргументы:
            guild_id: int - айди гильдии
        
        Возвращает:
            Имя коллекции mongodb
        """
        return f"shard{(guild_id >> 22) % self.__shard_count}"
    

    @timeit
    async def remove_guild(self, guild_id: int):
        """
        Метод удаления всей информации, связанной с гильдией

        Аргументы:
            guild_id: int - айди гильдии
        """
        logger.debug(f"removing all matches of the guild {guild_id}")
        try:
            await self.db[await self.get_shard(guild_id)].delete_many({'guild_id': guild_id})
        except Exception as E:
            logger.error(f"can't removing all matches of the guild {guild_id}: {E}")
        else:
            logger.debug(f"removing all mathces of the guild {guild_id} complete")
    
    @Correct_ids
    @timeit
    async def insert_user(self, guild_id, user_id):
        """
        Метод создания записи с информацией о пользователе в базе данных

        Модель пользователя: см. user_model.UserModel.get_json()

        Аргументы:
            guild_id: int - айди гильдии пользователя
            user_id: int - айди пользователя
        
        Возвращает:
            models.UserModel - объект пользователя (не discord.User, а кастомная оболочка)
        """
        logger.debug("inserting new user...")
        # Создаёт нового пользователя
        user = UserModel(user_id, guild_id)
        try:
            await self.db[await self.get_shard(guild_id)].insert_one(user.get_json())
        except Exception as E:
            logger.error(f'cant insert user: {E}')
        else:
            logger.debug('inserted new user')
            return user
    
    
    @timeit
    async def create_shop(self, guild_id: int):
        """
        Метод создания записи магазина для гильдии
        У каждой гильдии должна быть ровно 1 запись магазина гильдии в состоянии, когда бот является участником гильдии
        Бот стремится гарантировать создание магазина при присоединении к новой гильдии и удаление магазина при удалении бота из гильдии
        Если во время создания магазина произошла ошибка, он создастся при первой возможности, но уже при помощи метода fetch_user.
        Этот метод также используется в команде reset shop

        Особенность: id магазина всегда равно `минус guild_id` = `-guild_id` (guild_id=2312 => shop._id=-2312),
        это удобный способ, так как магазин ровно 1 на сервере

        Модель магазина: см. shop.get_shop()
        
        Аргументы:

        """
        logger.debug("creating shop")
        shop = get_shop(guild_id)
        try:
            await self.db[await self.get_shard(guild_id)].insert_one(shop)
        except Exception as E:
            logger.error(f'cant create shop: {E}')
        else:
            logger.debug('created shop')
            return shop
    
    
    @Correct_ids
    @timeit
    async def fetch_user(self, guild_id: int, user_id: int, **projection):
        """
        Метод для поиска пользователя или магазина в базе данных, если пользователь/магазин не найден, произойдёт его создание

        Аргументы:
            guild_id: int - айди гильдии
            user_id: int - айди пользователя
            projection: Dict[field: str, 1] - словарь полей, которые необходимо извлечь из записи в базе данных.
            Пример: user = await fetch_user(0, 0, money=1) - у user будут только поля _id и money, если пользователь уже есть в базе данных
        
        Возвращает:
            UserModel | dict | None
        """
        logger.debug("searching user")
        try:
            user = await self.db[await self.get_shard(guild_id)].find_one({'_id': user_id, 'guild_id': guild_id}, projection)
        except Exception as E:
            logger.debug(f'cant fetch user: {E}')
        else:
            if user is None:
                if user_id == -guild_id:
                    user = await self.create_shop(guild_id)
                    return user
                else:
                    user = await self.insert_user(guild_id, user_id)
                    return user.get_json()
            logger.debug("finded user")
            return user
    
    @timeit
    async def dblget_user_vote(self, user_id: int):
        """
        Метод отправляет запрос на сервис top.gg с целью проверки пользователя на предмет участия в голосовании за бота

        Аргументы:
            user_id: int - айди пользователя
        
        Возвращает:
            (int, dict) - статус запроса, полезная нагрузка
        """
        async with aioSession() as session:
            async with session.get(
                    self.__site_url + '/bots/883201346759704606/check', headers={
                        "Authorization": self.__dbl_token
                    }, params={
                        'userId': user_id
                        }
                ) as resp:
                return resp.status, await resp.json()

    @Correct_ids
    @timeit
    async def update_user(self, guild_id: int, user_id: int, query: dict):
        """
        Метод обновления данных о пользователе

        Аргументы:
            guild_id: int - айди гильдии
            user_id: int - айди пользователя
            query: Dict[command: str: Dict[arg: str, value: T]] Пример - (await update_user(0, 0, {'$push': {'inventory': i}, '$inc': {'money': -cost}}))
            Примеры ключей mongo лучше найти в интернете
        
        Особенность:
            Если пользователь не существует, создастся новая неполная запись (только с query полями),
            использовать только, когда известно, что запись о пользователе точно существует,
            например после fetch_user.
        """
        logger.debug("updating user...")
        logger.debug(f"updating: {query}")
        try:
            r = await self.db[await self.get_shard(guild_id)].update_one({'_id': user_id, 'guild_id': guild_id}, query, upsert=True)
        except Exception as E:
            logger.error(f'updating user error: {E}')
        else:
            logger.debug("updating user complete")
    
    
    @Correct_ids
    @timeit
    async def update_new(self, guild_id, user_id, query):
        """
        Метод изменения пользователя, когда мы не уверены, есть ли он в базе данных
        Используется в командах, которые не требуют получения информации при помощи fetch_user, а сразу изменяют её, например `give`

        Аргументы:
            guild_id: int - айди гильдии
            user_id: int - айди пользователя
            query: dict - словарь изменений Пример (update_new(0, 0, {'$set': {'color': theme}}))
        """
        logger.debug("updating user...")
        logger.debug(f"updating: {query}")
        try:
            r = await self.db[await self.get_shard(guild_id)].find_one_and_update({'_id': user_id, 'guild_id': guild_id}, query)
        except Exception as E:
            logger.error(f'updating user error: {E}')
        else:
            if r is None:
                if user_id == -guild_id:
                    await self.create_shop(guild_id)
                else:
                    await self.insert_user(guild_id, user_id)
                await self.update_user(guild_id, user_id, query)
            logger.debug("updating user complete")


    async def update_thread(self, query: list):
        """
        Асинхронная задача на запуск транзакции в базу данных и выполнение списка запросов query

        Аргументы:
            query: list - список запросов, которые нужно выполнить Пример query: [guild_id, user_id, {$inc: {params}}]
        """
        logger.debug(query)
        try:
            async with await self.start_session() as s:
                async with s.start_transaction():
                    for i in query:
                        coll = self.db[await self.get_shard(i[0])]
                        r = await coll.find_one_and_update({'_id': i[1], 'guild_id': i[0]}, i[2], session=s)
                        if r is None:
                            user = UserModel(i[1], i[0])
                            await coll.insert_one(user.get_json(), session=s)
                            await coll.update_one({'_id': i[1], 'guild_id': i[0]}, i[2], session=s)
        except Exception as E:
            logger.error(E)

    @timeit
    async def update_guild(self, guild_id: int, filter: dict, query: dict):
        """
        Команда изменения всех записей с айди гильдии guild_id

        Аргументы:
            guild_id: int - айди гильдии
            filter: dict - фильтр Пример ({'$ne': shop_id(ctx.guild.id)}}) - все, кроме магазина гильдии
            query: dict - какую операцию нужно выполнить к каждой записи Пример ({'$set': {'games': 0}})
        """
        try:
            await self.db[await self.get_shard(guild_id)].update_many({'guild_id': guild_id, **filter}, query, upsert=True)
        except Exception as E:
            logger.error(E)
    

    @timeit
    async def update_many(self, query: list):
        """
        query = [
            [guild_id, user_id, {$inc: {params}}]
        ]
        Метод для выполнения множества запросов сразу несколькими транзакциями

        Аргументы:
            query: list - двумерный список запросов запросов Пример ([[guild_id, user_id, {$inc: {params}}]])
            вложенный список можно воспринимать как целое - одна операция
        """
        # Создание списка задач
        threads_len = ceil(len(query) / self.__thread_size)
        threads = []
        for i in range(threads_len):
            threads.append(
                create_task(self.update_thread(
                    query[i * self.__thread_size : (i + 1) * self.__thread_size]
                ))
            )
        # И асинхронное выполнение сразу всех
        await gather(*threads)


    @Correct_ids
    @timeit
    async def delete_user(self, guild_id: int, user_id: int):
        """
        Метод удаления пользователя из базы данных

        Аргументы:
            guild_id: int - айди гильдии
            user_id: int - айди пользователя
        """
        logger.debug("deleting user...")
        try:
            await self.db[await self.get_shard(guild_id)].delete_one({'_id': user_id, 'guild_id': guild_id})
        except Exception as E:
            logger.error(f"can't delete user: {E}")
        else:
            logger.debug("deleting complete")

db = Database()
db.connect('casino_sharded')
