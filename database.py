from asyncio import get_event_loop, create_task, gather
from handlers import MailHandler
from logging import config, getLogger
from models.shop import get_shop
from models.user_model import UserModel
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import CollectionInvalid
from math import ceil
from os import environ
from time import time
from aiohttp import ClientSession as aioSession

config.fileConfig('./logging.ini', disable_existing_loggers=False)
logger = getLogger(__name__)
logger.addHandler(MailHandler())



class Database(AsyncIOMotorClient):

    __database_name = "casino"
    __mongo_password = environ.get("MONGO_PASSWORD")
    __thread_size = 30
    __dbl_token = environ.get("DBLTOKEN")
    __site_url = "https://top.gg/api"

    def __init__(self):
        pass

    def timeit(func):
        async def wrapper(self, *args, **kwargs):
            t0 = time()
            result = await func(self, *args, **kwargs)
            t1 = time()
            logger.debug(f'{func.__name__} done, time: {t1-t0}s')
            return result
        return wrapper
    
    def connect(self):
        logger.debug('connecting to cluster...')
        try:
            super().__init__(f"mongodb+srv://user:{self.__mongo_password}@cluster0.qbwbb.mongodb.net/{self.__database_name}?retryWrites=true&w=majority")
            logger.debug(self.server_info())
            self.db = self[self.__database_name]
            self.get_io_loop = get_event_loop
        except Exception as E:
            logger.critical(f"can't connect to database: {E}")
        else:
            logger.info(f"connected to database: {self.__database_name}")

    def Correct_ids(function):
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
        if isinstance(user_id, int):
            return True
        else:
            return False
    

    @timeit
    async def create_document(self, doc_name: str):
        """
        creating a  new document in __database_name database,
        doc_name: discord.Guild.id: string - document name
        return None
        """
        logger.debug(f"creating new document - {doc_name} in database {self.db.name}...")
        try:
            await self.db.create_collection(doc_name)
            await self.db[doc_name].insert_one(get_shop())
        except CollectionInvalid:
            try:
                await self.db[doc_name].insert_one(get_shop())
            except Exception as E:
                logger.error(f"can't create new document: {E}")
        except Exception as E:
            logger.error(f"can't create new document: {E}")
        else:
            logger.debug(f"{doc_name} created")
    
    @timeit
    async def delete_document(self, doc_name: str):
        """
        deleting a document in __database_name database,
        doc_name: discord.Guild.id: string - document name
        return None
        """
        logger.debug(f"deleting document - {doc_name} in database {self.db.name}...")
        try:
            await self.db.drop_collection(doc_name)
        except Exception as E:
            logger.error(f"can't delete document: {E}")
        else:
            logger.debug(f"{doc_name} deleted")
    
    @Correct_ids
    @timeit
    async def insert_user(self, guild_id, user_id):
        """
        inserting Usermodel: dict to database
        guild_id: int
        user_id: int
        return Usermodel
        """
        logger.debug("inserting new user...")
        user = UserModel(user_id)
        try:
            await self.db[guild_id.__str__()].insert_one(user.get_json())
        except Exception as E:
            logger.error(f'cant insert user: {E}')
        else:
            logger.debug('inserted new user')
            return user
    
    
    @timeit
    async def create_shop(self, guild_id):
        """
        create shop: dict to database
        guild_id: int
        return shop
        """
        logger.debug("creating shop")
        shop = get_shop()
        try:
            await self.db[guild_id.__str__()].insert_one(shop)
        except Exception as E:
            logger.error(f'cant create shop: {E}')
        else:
            logger.debug('created shop')
            return shop
    
    
    @Correct_ids
    @timeit
    async def fetch_user(self, guild_id, user_id, **projection):
        """
        getting Usermodel.json() : dict
        guild_id: int
        user_id: int
        projection: {field: 1,...}, use for optimize
        return Usermodel.json()
        """
        logger.debug("searching user")
        try:
            user = await self.db[guild_id.__str__()].find_one({'_id': user_id}, projection)
        except Exception as E:
            logger.debug(f'cant fetch user: {E}')
        else:
            if user is None:
                user = await self.insert_user(guild_id, user_id)
                return user.get_json()
            logger.debug("finded user")
            return user
    
    @timeit
    async def dblget_user_vote(self, user_id):
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
    async def update_user(self, guild_id, user_id, query):
        """
        updating Usermodel.json(): dict
        guild_id: int
        user_id: int
        params: Usermodel.slots params
        return None
        """
        logger.debug("updating user...")
        logger.debug(f"updating: {query}")
        try:
            r = await self.db[guild_id.__str__()].update_one({'_id': user_id}, query)
        except Exception as E:
            logger.error(f'updating user error: {E}')
        else:
            logger.debug("updating user complete")


    async def update_thread(self, query):
        logger.debug(query)
        try:
            async with await self.start_session() as s:
                async with s.start_transaction():
                    for i in query:
                        coll = self.db[str(i[0])]
                        await coll.update_one({'_id': i[1]}, i[2])
        except Exception as E:
            logger.error(E)

    @timeit
    async def update_guild(self, guild_id, filter, query):
        try:
            await self.db[str(guild_id)].update_many(filter, query)
        except Exception as E:
            logger.error(E)
    

    @timeit
    async def update_many(self, query):
        """
        query = [
            [guild_id, user_id, {$inc: {params}}]
        ]
        """
        threads_len = ceil(len(query) / self.__thread_size)
        threads = []
        for i in range(threads_len):
            threads.append(
                create_task(self.update_thread(
                    query[i * self.__thread_size : (i + 1) * self.__thread_size]
                ))
            )
        
        await gather(*threads)

    

    @timeit
    async def insert_many(self, guild_id, users_id: list):
        upd_users = []
        for i in users_id:
            upd_users.append(UserModel(i).get_json())

        await self.db[str(guild_id)].insert_many(upd_users)


    @Correct_ids
    @timeit
    async def delete_user(self, guild_id, user_id):
        logger.debug("deleting user...")
        try:
            await self.db[guild_id.__str__()].delete_one({'_id': user_id})
        except Exception as E:
            logger.error(f"can't delete user: {E}")
        else:
            logger.debug("deleting complete")

db = Database()
db.connect()
