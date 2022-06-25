from datetime import time
from typing import Any, Dict

settings: Dict[str, Any] = {
    "log.dir": "Z:/log/",

    "symbol.day": {"UR","JD","AP","SM","SF","LH"},

    "database.name": "database.db",
    "database.host": "localhost",
    "database.port": 27017,
    "database.username": "",
    "database.password": "",

    "tradingtime.day_start": time(8, 45),
    "tradingtime.day_end": time(15, 0),
    "tradingtime.night_start": time(20, 45),
    "tradingtime.night_end": time(2, 45),
}