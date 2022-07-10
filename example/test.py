from dataclasses import dataclass
from datetime import datetime, time

from pymongo import MongoClient
from base.database import MongoDatabase
from base.setting import settings
import re
@dataclass
class Test():
    b:str
    def __init__(self) -> None:
        self.a = 1

        if self.a>11:
            self.b = 12

    def fun(self):
        if self.a:
            print(self.a)

    def fun2(self):
        if self.b:
            print(self.b)

if __name__ == "__main__":
    
    # mongo = MongoDatabase()
    # data = mongo.load_bar_data("rb2210", "20220708")
    # for i in data:
    #     print(i)
    # print(len(data))
    test = Test()
    # test.fun2()
    # d = {"test": test}
    # print(d.get("test").a)
    # test.a = 122
    # print(d.get("test").a)