from enum import Enum

class OrderRequestType(Enum):
    BUY = "open buy"
    SELL = "close sell"
    SHORT = "open sell"
    COVER = "close buy"

class ContractStatus(Enum):
    BEFOR_TRADING = "开盘前"
    NO_TRADING = "非交易"
    CONTINOUS = "连续交易"
    AUCTION_ORDERING = "集合竞价报单"
    AUCTION_BALANCE = "集合竞价价格平衡"
    AUCTION_MATCH = "集合竞价撮合"
    CLOSED = "收盘"