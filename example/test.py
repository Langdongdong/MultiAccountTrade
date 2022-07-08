from datetime import datetime, time

from pymongo import MongoClient
from base.database import MongoDatabase
from base.setting import settings
import re

if __name__ == "__main__":
    # a = set()
    # for i in settings.get("symbol.tradingtime").keys():
    #     a.add(i)

    # a = set(a)
    mongo = MongoDatabase()
    data = mongo.load_bar_data("rb2210", "20220708")
    for i in data:
        print(i)
    print(len(data))