from datetime import datetime
from typing import Any, Dict

from vnpy_ctp import CtpGateway
from vnpy_rohon import RohonGateway

settings: Dict[str, Any] = {
    "log.dir": "Z:/log/",

    "symbol.day": {"UR","JD","AP","SM","SF","LH"},

    "tradingtime.daystart": datetime.time(8, 45),
    "tradingtime.dayend": datetime.time(15, 0),
    "tradingtime.nightstart": datetime.time(20, 45),
    "tradingtime.nightend": datetime.time(2, 45),
}