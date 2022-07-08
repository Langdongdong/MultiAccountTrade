from decimal import Decimal
import numpy

from typing import Any, Callable, Dict, Optional, Sequence

from numpy import ndarray
from pandas import DataFrame

from vnpy.trader.object import BaseData, TickData

from .object import BarData

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
    Only generate minute bar.
    """
    def __init__(self, period: int = 1) -> None:
        self.period: int = period

        self.bars: Dict[str, BarData] = {}
        self.last_ticks: Dict[str, TickData] = {}
        self.period_counts: Dict[str, int] = {}

    def update_tick(self, tick: TickData, on_bar: Callable) -> Optional[BarData]:
        last_tick: TickData = self.last_ticks.get(tick.vt_symbol)

        if not tick.last_price:
             return 

        if last_tick and tick.datetime < last_tick.datetime:
            return

        bar: BarData = self.bars.get(tick.vt_symbol)
        period_count: int = self.period_counts.get(tick.vt_symbol, 0)
        
        if bar and bar.date.minute != tick.datetime.minute:
            period_count += 1
            if self.period == period_count:
                period_count = 0

                bar.date = bar.date.replace(second=0, microsecond=0)
                for k, v in bar.__dict__.items():
                    if type(v) == float:
                        setattr(bar, k, float(Decimal.from_float(v).quantize(Decimal('0.00'))))
                        
                on_bar(self.bars.pop(tick.vt_symbol))
                
            self.period_counts[tick.vt_symbol] = period_count
                
        if not bar:
            self.bars[tick.vt_symbol] = BarData(
                symbol = tick.symbol,
                open = tick.last_price,
                close = tick.last_price,
                high = tick.last_price,
                low = tick.last_price,
                avg = None,
                high_limit = tick.limit_up,
                low_limit = tick.limit_down,
                pre_close = tick.pre_close,
                open_interest = tick.open_interest,
                date = tick.datetime
            )
        else:
            bar.date = tick.datetime
            bar.close = tick.last_price
            bar.open_interest = tick.open_interest

            bar.high = max(tick.last_price, bar.high)
            if tick.high_price > last_tick.high_price:
                bar.high = max(tick.high_price, bar.high)

            bar.low = min(tick.last_price, bar.low)
            if tick.low_price < last_tick.low_price:
                bar.low = min(tick.low_price, bar.low)

        if last_tick:
            bar.volume += max(tick.volume - last_tick.volume, 0)
            bar.money += max(tick.turnover - last_tick.turnover, 0)

        self.last_ticks[tick.vt_symbol] = tick

class ArrayManager:
    def __init__(self, size: int = 1) -> None:
        self.size: int = size

        self.open_array: Dict[str, ndarray] = {}
        self.close_array: Dict[str, ndarray] = {}
        self.high_array: Dict[str, ndarray] = {}
        self.low_array: Dict[str, ndarray] = {}
        self.volume_array: Dict[str, ndarray] = {}
        self.money_array: Dict[str, ndarray] = {}
        self.open_interest_array: Dict[str, ndarray] = {}


    def udpate_bar(self, bar: BarData) -> None:
        if not self.open_array.get(bar.symbol):
            self.open_array[bar.symbol] = numpy.zeros(self.size)
            self.close_array[bar.symbol] = numpy.zeros(self.size)
            self.high_array[bar.symbol] = numpy.zeros(self.size)
            self.low_array[bar.symbol] = numpy.zeros(self.size)
            self.volume_array[bar.symbol] = numpy.zeros(self.size)
            self.money_array[bar.symbol] = numpy.zeros(self.size)
            self.open_interest_array[bar.symbol] = numpy.zeros(self.size)
        
        open_array: ndarray = self.open_array.get(bar.symbol)
        close_array: ndarray = self.close_array.get(bar.symbol)
        high_array: ndarray = self.high_array.get(bar.symbol)
        low_array: ndarray = self.low_array.get(bar.symbol)
        volume_array: ndarray = self.volume_array.get(bar.symbol)
        money_array: ndarray = self.money_array.get(bar.symbol)
        open_interest_array: ndarray = self.open_interest_array.get(bar.symbol)

        open_array[:-1] = open_array[1:]
        close_array[:-1] = close_array[1:]
        high_array[:-1] = high_array[1:]
        low_array[:-1] = low_array[1:]
        volume_array[:-1] = volume_array[1:]
        money_array[:-1] = money_array[1:]
        open_interest_array[:-1] = open_interest_array[1:]

        open_array[-1] = bar.open
        close_array[-1] = bar.close
        high_array[-1] = bar.high
        low_array[-1] = bar.low
        volume_array[-1] = bar.volume
        money_array[-1] = bar.money
        open_interest_array[-1] = bar.open_interest

    @property
    def open(self) -> ndarray:
        return self.open_array

    @property
    def close(self) -> ndarray:
        return self.close_array
    
    @property
    def high(self) -> ndarray:
        return self.high_array

    @property
    def low(self) -> ndarray:
        return self.low_array

    @property
    def volume(self) -> ndarray:
        return self.volume_array

    @property
    def money(self) -> ndarray:
        return self.money_array

    @property
    def open_interst(self) -> ndarray:
        return self.open_interest_array