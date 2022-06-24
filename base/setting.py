from datetime import datetime
from typing import Any, Dict

settings: Dict[str, Any] = {
    "log.dir": "Z:/log/",

    "symbol.day": {"UR","JD","AP","SM","SF","LH"},

    "database.name": "database.db",
    "database.host": "",
    "database.port": 0,
    "database.username": "",
    "database.password": "",

    "trading_time.day_start": datetime.time(8, 45),
    "trading_time.day_end": datetime.time(15, 0),
    "trading_time.night_start": datetime.time(20, 45),
    "trading_time.night_end": datetime.time(2, 45),
}