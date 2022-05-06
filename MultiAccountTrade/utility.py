from typing import Any, Callable, Optional, Sequence

from pandas import DataFrame
from constant import *
from vnpy.trader.object import BaseData
from vnpy.trader.constant import Exchange


def is_trade_period() -> bool:
    cur_time = datetime.datetime.now().time()
    if (
        DAY_START <= cur_time <= DAY_END
        or NIGHT_START <= cur_time
        or NIGHT_END >= cur_time
    ):
        if datetime.time(9,5) <= cur_time or datetime.time(21,5) <= cur_time:
            return True
    return False


def is_day_period() -> bool:
    cur_time = datetime.datetime.now().time()
    if DAY_START <= cur_time <= DAY_END:
        return True
    return False


def is_night_period() -> bool:
    cur_time = datetime.datetime.now().time()
    if (NIGHT_START <= cur_time) or (NIGHT_END >= cur_time):
        return True
    return False

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

    
def convert_to_symbol(vt_symbol: str) -> str:
    spl = vt_symbol.split(".")

    pre = spl[0].upper()
    suf = spl[1]

    if suf == Exchange.CZCE.value:
        suf = "CZC"
    elif suf == Exchange.SHFE.value:
        suf = "SHF"

    return f"{pre}.{suf}"


def to_df(data_list: Sequence) -> Optional[DataFrame]:
    if not data_list:
        return None
    
    dict_list: list = [data.__dict__ for data in data_list]
    return DataFrame(dict_list)


def get_df(data: Any, use_df: bool = False) -> Optional[BaseData]:
    if not use_df or data is None:
        return data
    else:
        if not isinstance(data, list):
            data = [data]
        return to_df(data)


def convert_to_vt_order_type(Op1: str, Op2: str) -> OrderMode:
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


def convert_to_order_type(order_type: OrderMode) -> tuple:
    if order_type == OrderMode.BUY:
        return "Open", "Buy"
    elif order_type == OrderMode.SHORT:
        return "Open", "Sell"
    elif order_type == OrderMode.COVER:
        return "Close", "Buy"
    elif order_type == OrderMode.SELL:
        return "Close", "Sell"