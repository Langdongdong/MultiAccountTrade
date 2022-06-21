from typing import Any, Callable, Dict, Optional, Sequence

from pandas import DataFrame
from vnpy.event import Event, EventEngine
from vnpy.trader.event import EVENT_TICK
from vnpy.trader.constant import Interval
from vnpy.trader.object import BaseData, TickData, BarData

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
