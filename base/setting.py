import logging

from datetime import time
from typing import Any, Dict

settings: Dict[str, Any] = {
    "log.active": True,
    "log.level": logging.INFO,
    "log.console": True,
    "log.file": False,
    "log.dir": "E:/log/",


    "symbol.day": {"SM", "SF", "WH", "JR", "LR", "PM", "RI", "RS", "PK", "UR", "CJ", "AP", "bb", "fb", "lh", "jd", "wr", "IF", "IC", "IH", "T", "TF", "TS"},
    "symbol.tradingtime":{
        ("IF", "IC", "IH"): (time(9,30), time(11,30), time(13,0), time(15,0)),
        ("T", "TF", "TS"): (time(9,15), time(11,30), time(13,0), time(15,15)),
        ("SM", "SF", "WH", "JR", "LR", "PM", "RI", "RS", "PK", "UR", "CJ", "AP", "bb", "fb", "lh", "jd", "wr"): (time(9,0), time(10,15), time(10,30), time(11,30), time(13,30), time(15,0)),
        ("FG", "SA", "MA", "SR", "TA", "RM", "OI", "CF", "CY", "PF", "ZC", "i", "j", "jm", "a", "b", "m", "p", "y", "c", "cs", "pp", "v", "eb", "eg", "pg", "rr", "l", "fu", "ru", "bu", "sp", "rb", "hc", "lu", "nr"): (time(9,0), time(10,15), time(10,30), time(11,30), time(13,30), time(15,0), time(21,0), time(23,0)),
        ("cu", "pb", "al", "zn", "sn", "ni", "ss", "bc"): (time(9,0), time(10,15), time(10,30), time(11,30), time(13,30), time(15,0), time(21,0), time(1,0)),
        ("au", "ag", "sc"): (time(9,0), time(10,15), time(10,30), time(11,30), time(13,30), time(15,0), time(21,0), time(2,30)),
    },

    "database.name": "db_bar_min",
    "database.host": "localhost",
    "database.port": 27017,
    "database.username": "",
    "database.password": "",

    "tradingtime.day": (time(8, 55), time(15,20)),
    "tradingtime.night": (time(20, 55), time(2, 35)),
}