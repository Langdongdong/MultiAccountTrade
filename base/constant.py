from enum import Enum

class OrderRequestType(Enum):
    BUY = "open buy"
    SELL = "close sell"
    SHORT = "open sell"
    COVER = "close buy"