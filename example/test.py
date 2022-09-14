import sys
sys.path.append(".")
from dataclasses import dataclass
from datetime import datetime, time, timedelta

from pymongo import MongoClient
from base.database import MongoDatabase
from base.setting import SETTINGS
import re

from pytz import timezone
from tzlocal import get_localzone_name

import asyncio
import random
import time


async def worker(name, queue):
    while True:
        # Get a "work item" out of the queue.
        sleep_for = await queue.get()

        # Sleep for the "sleep_for" seconds.
        await asyncio.sleep(sleep_for)

        # Notify the queue that the "work item" has been processed.
        queue.task_done()

        print(f'{name} has slept for {sleep_for:.2f} seconds')


async def main():
    # Create a queue that we will use to store our "workload".
    queue = asyncio.Queue()

    # Generate random timings and put them into the queue.
    total_sleep_time = 0
    for _ in range(20):
        sleep_for = random.uniform(0.05, 1.0)
        total_sleep_time += sleep_for
        queue.put_nowait(sleep_for)

    # Create three worker tasks to process the queue concurrently.
    tasks = []
    for i in range(3):
        task = asyncio.create_task(worker(f'worker-{i}', queue))
        tasks.append(task)

    # Wait until the queue is fully processed.
    started_at = time.monotonic()
    await queue.join()
    total_slept_for = time.monotonic() - started_at

    # Cancel our worker tasks.
    # for task in tasks:
    #     task.cancel()
    # Wait until all worker tasks are cancelled.
    # await asyncio.gather(*tasks, return_exceptions=True)

    print('====')
    print(f'3 workers slept in parallel for {total_slept_for:.2f} seconds')
    print(f'total expected sleep time: {total_sleep_time:.2f} seconds')


asyncio.run(main())
# if __name__ == "__main__":
    
#     # mongo = MongoDatabase()
#     # data = mongo.load_bar_data("au2212", datetime.strptime("20220904","%Y%m%d"),datetime.strptime("20220908","%Y%m%d"))
#     # for i in data: 
#     #     print(i)
#     # print(len(data))

#     now = datetime.now()
#     print(now)
#     now.replace(tzinfo= timezone(get_localzone_name()))
#     print(now, now.tzinfo)


#     # print(datetime.now() - timedelta(minutes=1))
#     # print(datetime.now().tzinfo)
#     # print(datetime.now() < datetime.now()+timedelta(minutes=1))

    