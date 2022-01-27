from asyncio import sleep
import time
from database import db
from time import strftime, strptime

class Data():
    def __init__(self):
        self.start_time = time.time()
        self.per_minute = 0
        self.per_hour = 0
    
    async def on_command(self):
        self.per_minute += 1
        self.per_hour += 1
    
    
    async def get_minute(self):
        m = self.per_minute
        self.per_minute = 0
        return m

    async def get_hour(self):
        m = self.per_hour
        self.per_hour = 0
        return m
    
    async def acstime(self):
        '%Y:%j:%H:%M'
    
    async def write_minute(self):
        q = await db.db['time'].update_one({
            '_id': strftime('%Y:%j')
            }, {
                '$push': {strftime('%H') + '.minutes': await self.get_minute()}
                }, upsert=True)
    
    async def write_hour(self):
        q = await db.db['time'].update_one({
            '_id': strftime('%Y:%j')
            }, {
                '$set': {strftime('%H') + '.hour': await self.get_minute()}
                }, upsert=True)
    
    
    async def loop(self):
        while True:
            if (time.time() - self.start_time) % 3600 < 60:
                await self.write_hour()
            await self.write_minute()
            await sleep(60 - ((time.time() - self.start_time) % 60))