import asyncio
from random import randint
from time import time

InsertTask = "InsertTask"
UpdateTask = "UpdateTask"
DeleteTask = "DeleteTask"

GetQuery = "GetQuery"
RemoveManyQuery = "RemoveManyQuery"
AddQuery = "AddQuery"
RemoveOneQuery = "RemoveOneQuery"


class Task():
    def __init__(self, query: tuple, task: object):
        self.__query = query
        self.__task = task
    
    @property
    def query(self):
        return self.__query
    
    @property
    def task(self):
        return self.__task



class Queue():

    def __que(self):
        que = []
        while True:
            try:
                data = yield que
            except StopIteration:
                return que
            else:
                if not data is None:
                    if data[0] is AddQuery:
                        que.extend(data[1])
                    elif data[0] is RemoveOneQuery:
                        que.remove(data[1])
                    elif data[0] is RemoveManyQuery:
                        for i in data[1]:
                            que.remove(i)
    
    def __init__(self):
        self.__q = self.__que()
        self.__q.send(None)
    
    async def __send(self, query):
        r = self.__q.send(query)
        return r
    
    async def get(self):
        r = await self.__send([GetQuery])
        return r
    
    async def add(self, query: list):
        await self.__send([AddQuery, query])
    
    async def remove_many(self, query: list):
        await self.__send([RemoveManyQuery, query])

q = Queue()

async def getter():
    while True:
        t = time()
        r = await q.get()
        print(len(r))
        await asyncio.sleep(0.001)

async def setter():
    while True:
        await q.add([Task(({'_id': 397352286487052288}, {'$inc': {'money': randint(1, 1000)}}), UpdateTask) for i in range(randint(0, 3))])
        await asyncio.sleep(0.001)

async def deleter():
    while True:
        r = await q.get()
        l = len(r)
        start = randint(0, l)
        finish = randint(start, l)
        await q.remove_many(r[start:finish])
        await asyncio.sleep(0.001)

async def main():
    t1 = asyncio.create_task(getter())
    t2 = asyncio.create_task(setter())
    t3 = asyncio.create_task(deleter())
    await asyncio.gather(t1, t2, t3)

if __name__ == '__main__':
    asyncio.run(main())
