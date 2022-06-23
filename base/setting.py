from datetime import datetime
from typing import Any, Dict

settings: Dict[str, Any] = {
    "log.dir": "Z:/log/",

    "symbol.day": {"UR","JD","AP","SM","SF","LH"},

    "database.host": "",
    "database.port": "",
    "database.username": "",
    "database.password": "",

    "tradingtime.daystart": datetime.time(8, 45),
    "tradingtime.dayend": datetime.time(15, 0),
    "tradingtime.nightstart": datetime.time(20, 45),
    "tradingtime.nightend": datetime.time(2, 45),
}