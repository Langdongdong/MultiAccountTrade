import datetime

from enum import Enum

DAY_START = datetime.time(9, 0)
DAY_END = datetime.time(15, 0)

NIGHT_START = datetime.time(21, 0)
NIGHT_END = datetime.time(2, 45)

class OrderMode(Enum):
    BUY = "open buy"
    SELL = "close sell"
    SHORT = "open sell"
    COVER = "close buy"

class BacktestingMode(Enum):
    BAR = "bar"
    TICK = "tick"