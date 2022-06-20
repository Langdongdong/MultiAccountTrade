from typing import Any, Callable, Dict, Optional, Sequence
from copy import deepcopy
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
    Generate n minute bars.
    """
    def __init__(self, period: int = 1, on_bar: Callable = None) -> None:
        self.period: int = period
        self.on_bar: Callable = on_bar

        self.bars: Dict[str, BarData] = {}
        self.last_ticks: Dict[str, TickData] = {}
        self.period_counts: Dict[str, int] = {}

    def update_minute_bar(self, tick: TickData) -> None:
        bar: BarData = self.bars.get(tick.vt_symbol)
        last_tick: TickData = self.last_ticks.get(tick.vt_symbol)
        period_count: int = self.period_counts.get(tick.vt_symbol, 0)
        
        if not period_count or not self.period % period_count:
            if bar:
                bar.datetime.replace(second=0, microsecond=0)
                self.on_bar(bar)
                self.period_counts[tick.vt_symbol] = 0

            self.bars[tick.vt_symbol] = BarData(
                gateway_name = tick.gateway_name,
                symbol = tick.symbol,
                exchange = tick.exchange,
                datetime = tick.datetime,
                interval = Interval.MINUTE,
                open_interest = tick.open_interest,
                open_price = tick.last_price,
                high_price = tick.last_price,
                low_price = tick.last_price,
                close_price = tick.low_price
            )

        else:
            bar.datetime = tick.datetime
            bar.close_price = tick.last_price
            bar.open_interest = tick.open_interest

            bar.high_price = max(tick.high_price, bar.high_price)
            bar.low_price = min(tick.low_price, bar.low_price)

            bar.volume += max(tick.volume - last_tick.volume, 0)
            bar.turnover += max(tick.turnover - last_tick.turnover, 0)

            if bar.datetime.min != last_tick.datetime.min:
                period_count += 1
                self.period_counts[tick.vt_symbol] = period_count

        self.last_ticks[tick.vt_symbol] = tick
