from typing import Any, Optional, Sequence

from pandas import DataFrame
from constant import *
from vnpy.trader.object import BaseData


def is_trade_period() -> bool:
    cur_time = datetime.datetime.now().time()
    if (
        DAY_START <= cur_time <= DAY_END
        or NIGHT_START <= cur_time
        or NIGHT_END >= cur_time
    ):
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