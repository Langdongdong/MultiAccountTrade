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


if __name__ == "__main__":
    
    # mongo = MongoDatabase()
    # data = mongo.load_bar_data("au2212", datetime.strptime("20220904","%Y%m%d"),datetime.strptime("20220908","%Y%m%d"))
    # for i in data: 
    #     print(i)
    # print(len(data))

    now = datetime.now()
    print(now)
    now.replace(tzinfo= timezone(get_localzone_name()))
    print(now, now.tzinfo)


    # print(datetime.now() - timedelta(minutes=1))
    # print(datetime.now().tzinfo)
    # print(datetime.now() < datetime.now()+timedelta(minutes=1))