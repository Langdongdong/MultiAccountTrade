from enum import Enum

class OrderMode(Enum):
    BUY = "open buy"
    SELL = "close sell"
    SHORT = "open sell"
    COVER = "close buy"