from datetime import datetime, time

from pymongo import MongoClient
from base.database import MongoDatabase
from base.setting import settings
import re

class Test():
    a = 11

if __name__ == "__main__":
    
    # mongo = MongoDatabase()
    # data = mongo.load_bar_data("rb2210", "20220708")
    # for i in data:
    #     print(i)
    # print(len(data))
    test = Test()
    d = {"test": test}
    print(d.get("test").a)
    test.a = 122
    print(d.get("test").a)