import motor.motor_asyncio
import os
import time
import asyncio
from random import randint
from server import Queue


client = motor.motor_asyncio.AsyncIOMotorClient(f"mongodb+srv://user:{os.environ.get('MONGO_PASSWORD')}@cluster0.qbwbb.mongodb.net/{'casino'}?retryWrites=true&w=majority")
db = client['casino']
client.get_io_loop = asyncio.get_running_loop


q = Queue()

async def do_update(guild_id, user_id, query):
    coll = db[str(guild_id)]
    result = await coll.insert_many(query)
    return result


async def handler2():
    while True:
        t = [ {'user_name': randint(1, 100), 'money': randint(100, 1000), 'level': randint(1000, 10000), 'exp': randint(1, 1000000)} for i in range(randint(1, 100)) ]
        await q.add(t)
        print('tasks added:', t)
        await asyncio.sleep(5)


async def handler3():
    while True:
        tasks = await q.get()
        print(tasks)
        if len(tasks) > 0:
            print(len(tasks))
            r = await do_update(750791175606239397, 397352286487052288, tasks)
            print(r)
            await q.remove(tasks)
        else:
            await asyncio.sleep(1)
tasks = [
    [750791175606239397, 397352286487052288, {'money': 100}] for i in range(100)
]

async def job(iter):
    t0 = time.time()
    async with await client.start_session() as s:
        async with s.start_transaction():
            for t, i in enumerate(tasks):
                coll = db[i[0].__str__()]
                await coll.update_one({'_id': i[1]}, {'$inc': i[2]})
                print(t)
    t1 = time.time()
    print(f"finished {iter}: {t1 - t0}s")


async def main():
    tasks = []
    for i in range(10):
        tasks.append(asyncio.create_task(job(i)))

    await asyncio.gather(*tasks)

asyncio.run(main())
print('finished')