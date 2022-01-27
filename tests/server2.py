import asyncio
from random import randint
from server import Task, UpdateTask
from time import time
p = []

async def getter():
    while True:
        t = time()
        r = p
        print(len(r))
        await asyncio.sleep(0.001)

async def setter():
    while True:
        p.append([Task(({'_id': 397352286487052288}, {'$inc': {'money': randint(1, 1000)}}), UpdateTask)] for i in range(randint(0, 100)))
        await asyncio.sleep(0.001)

async def deleter():
    global p
    while True:
        r = p
        l = len(r)
        start = randint(0, l)
        finish = randint(start, l)
        to_bin = r[start:finish]
        p = [i for i in r if i not in to_bin]
        await asyncio.sleep(0.001)

async def main():
    t1 = asyncio.create_task(getter())
    t2 = asyncio.create_task(setter())
    t3 = asyncio.create_task(deleter())
    await asyncio.gather(t1, t2, t3)

if __name__ == '__main__':
    asyncio.run(main())