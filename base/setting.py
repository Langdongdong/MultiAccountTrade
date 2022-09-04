import logging

from datetime import time
from typing import Any, Dict

SETTINGS: Dict[str, Any] = {
    "log.active": True,
    "log.level": logging.INFO,
    "log.console": True,
    "log.file": False,
    "log.dir": "D:/log/",

    "database.database": "db_ctp",
    "database.host": "localhost",
    "database.port": 27017,
    "database.username": "",
    "database.password": "",

    "tickfilter.active": True,
    "tickfilter.latency": 120,  # second unit

    "tradingtime.day": (time(8, 55), time(15,20)),
    "tradingtime.night": (time(20, 55), time(2, 35)),

    "symbol.day": {"SM", "SF", "WH", "JR", "LR", "PM", "RI", "RS", "PK", "UR", "CJ", "AP", "bb", "fb", "lh", "jd", "wr", "IF", "IC", "IH", "T", "TF", "TS"},
    "symbol.tradingtime":{
        ("IF", "IC", "IH", "IM"): (time(9,30), time(11,30), time(13,0), time(15,0)),
        ("T", "TF", "TS"): (time(9,30), time(11,30), time(13,0), time(15,15)),
        ("SM", "SF", "WH", "JR", "LR", "PM", "RI", "RS", "PK", "UR", "CJ", "AP", "bb", "fb", "lh", "jd", "wr"): (time(9,0), time(10,15), time(10,30), time(11,30), time(13,30), time(15,0)),
        ("FG", "SA", "MA", "SR", "TA", "RM", "OI", "CF", "CY", "PF", "ZC", "i", "j", "jm", "a", "b", "m", "p", "y", "c", "cs", "pp", "v", "eb", "eg", "pg", "rr", "l", "fu", "ru", "bu", "sp", "rb", "hc", "lu", "nr"): (time(9,0), time(10,15), time(10,30), time(11,30), time(13,30), time(15,0), time(21,0), time(23,0)),
        ("cu", "pb", "al", "zn", "sn", "ni", "ss", "bc"): (time(9,0), time(10,15), time(10,30), time(11,30), time(13,30), time(15,0), time(21,0), time(1,0)),
        ("au", "ag", "sc"): (time(9,0), time(10,15), time(10,30), time(11,30), time(13,30), time(15,0), time(21,0), time(2,30)),
    },
}

ACCOUNTS: Dict[str, Any] = {
    # "DDTEST0": {
    #     "用户名": "20177599",
    #     "密码": "19910703",
    #     "经纪商代码": "8080",
    #     "交易服务器": "27.115.78.182:41206",
    #     "行情服务器": "27.115.78.182:41214",
    #     "产品名称": "client_gwqtrader_v1.0.0",
    #     "授权编码": "L8WN410RZ28OJM3X",
    #     "gateway": CtpGateway
    # },
    "ZHONGYINQIHUO": {
        "用户名": "91600338",
        "密码": "dd027232",
        "经纪商代码": "5040",
        "交易服务器": "180.169.95.243:21205",
        "行情服务器": "220.248.39.103:21213",
        "产品名称": "client_ddtrader_v1.0.0",
        "授权编码": "GFB98U1HSAZJEZNE",
        "gateway": CtpGateway
    },
}