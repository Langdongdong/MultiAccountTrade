from typing import Any, Optional, Sequence

from pandas import DataFrame
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

class BarGenerator:
    """
    Generate minute bar.
    """
    def __init__(self, period: int = 1) -> None:
        self.period: int = period
        self.period_count: int = 0

        self.last_bar: BarData = None
        self.last_tick: TickData = None

    def get_bar(self, tick: TickData) -> Optional[BarData]:
        if not self.last_tick:
            return
        
        if self.last_tick and tick.datetime < self.last_tick.datetime:
            return
        
        if (not self.last_bar) or (not self.period_count % self.period):
            
            self.last_bar = BarData(
                symbol = tick.symbol,
                exchange = tick.exchange,
                interval = Interval.MINUTE,
                datetime = tick.datetime,
                gateway_name = tick.gateway_name,
                open_price = tick.last_price,
                high_price = tick.last_price,
                low_price = tick.last_price,
                close_price = tick.last_price,
                open_interest = tick.open_interest
            )
            self.last_bar.datetime.replace(second=0, microsecond=0)

        else:
            
            self.last_bar.datetime = tick.datetime
            self.last_bar.close_price = tick.last_price
            self.last_bar.open_interest = tick.open_interest
            
            self.last_bar.high_price = max(tick.high_price, tick.last_price, self.last_bar.high_price)
            self.last_bar.low_price = min(tick.low_price, tick.last_price, self.last_bar.low_price)

            self.last_bar.volume += max(tick.volume - self.last_tick.volume, 0)
            self.last_bar.turnover += max(tick.turnover - self.last_tick.turnover, 0)

        self.last_tick = tick