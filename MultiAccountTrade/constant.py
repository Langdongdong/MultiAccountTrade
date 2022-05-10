import datetime

from enum import Enum

DAY_START = datetime.time(8, 45)
DAY_END = datetime.time(15, 0)

NIGHT_START = datetime.time(20, 45)
NIGHT_END = datetime.time(2, 45)


SYMBOL_AM = ["UR","JD","AP","SM","SF","LH"]


TWAP_SETTING = {
    "TIME": 60, 
    "INTERVAL" : 30
}

# 180.168.146.187:10201
# 180.168.146.187:10211
# 180.168.146.187:10130
# 180.168.146.187:10131
CTP_SETTING = {
    "用户名": "083231",
    "密码": "wodenvshen199!",
    "经纪商代码": "9999",
    "交易服务器": "180.168.146.187:10201",
    "行情服务器": "180.168.146.187:10211",
    "产品名称": "0000000000000000",
    "授权编码": "0000000000000000",
}


CSV_SETTING = {
    "CSV_ORDER_DIR_PATH" : "Z:/position/TRADE/",
    "CSV_POS_DIR_PATH" : "Z:/HOLD/",
    "CSV_BACKUP_DIR_PATH" : "D:/vnpy_trade/BACKUP/",
    "CSV_ACCOUNT" : "DDTEST",
}


TRADE_TIME_SETTING = {
    "DAY_START": datetime.time(9, 0),
    "DAT_END": datetime.time(15, 0),
    "NIGHT_START": datetime.time(21, 0),
    "NIGHT_END": datetime.time(23, 0)
}


class OrderMode(Enum):
    BUY = "OPEN_BUY"
    SELL = "CLOSE_SELL"
    SHORT = "OPEN_SELL"
    COVER = "CLOSE_BUY"