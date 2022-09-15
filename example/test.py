from glob import glob
import importlib
from pathlib import Path
import sys
from types import ModuleType
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


from strategy.template import CtaTemplate


if __name__ == "__main__":
    
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
    path = Path.cwd().joinpath("strategy")

    for suffix in ["py", "pyd", "so"]:
        pathname: str = str(path.joinpath(f"*.{suffix}"))
        for filepath in glob(pathname):
            filename = Path(filepath).stem
            module_name: str = f"{'strategy'}.{filename}"

            module: ModuleType = importlib.import_module(module_name)
            
            importlib.reload(module)

            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, CtaTemplate) and value is not CtaTemplate):
                    print(value)
