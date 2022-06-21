from dataclasses import dataclass
from datetime import datetime

import pandas

from utility import to_df
from constant import OrderMode
from vnpy.trader.constant import Exchange

@dataclass
class OrderAsking:
    ContractID: str
    Op1: str
    Op2: str
    volume: float

    def __post_init__(self) -> None:
        self.vt_symbol = OrderAsking.convert_to_vt_symbol(self.ContractID)
        self.order_mode = OrderAsking.convert_to_vt_order_mode(self.Op1, self.Op2)

    @staticmethod
    def convert_to_vt_symbol(symbol: str) -> str:
        spl = symbol.split(".")
        pre = spl[0].lower()
        suf = spl[1]

        if suf == "CZC":
            pre = pre.upper()
            suf = Exchange.CZCE.value

        elif suf == "SHF":
            suf = Exchange.SHFE.value

        return f"{pre}.{suf}"

    @staticmethod
    def convert_to_vt_order_mode(Op1: str, Op2: str) -> OrderMode:
        if Op1 == "Open":
            if Op2 == "Buy":
                return OrderMode.BUY
            else:
                return OrderMode.SHORT
        else:
            if Op2 == "Buy":
                return OrderMode.COVER
            else:
                return OrderMode.SELL

@dataclass
class MongodbBar:
    symbol: str
    open: float = 0
    close: float = 0
    high: float = 0
    low: float = 0
    volume: float = 0
    money: float = 0
    avg: float = 0
    high_limit: float = 0
    low_limit: float = 0
    pre_close: float = 0
    open_interest: float = 0
    date: datetime = None

    def to_df(self) -> pandas.DataFrame:
         return pandas.DataFrame([self.__dict__])