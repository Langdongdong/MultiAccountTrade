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

# class BarGenerator:
#     """
#     Generate n minute bars.
#     """
#     def __init__(self, event_engine: EventEngine, period: int = 1, on_bar: Callable = None) -> None:
#         self.event_engine: EventEngine =  event_engine
#         self.period: int = period
#         self.on_bar: Callable = on_bar

#         self.bars: Dict[str, BarData] = {}
#         self.last_ticks: Dict[str, TickData] = {}
#         self.period_counts: Dict[str, int] = {}

#         self._register_tick_process()

#     def _register_tick_process(self) -> None:
#         self.event_engine.register(EVENT_TICK, self._process_tick_event)

#     def _process_tick_event(self, event: Event):
#         tick: TickData = event.data
#         self.update_minute_bar(tick)

#     def update_minute_bar(self, tick: TickData) -> None:
#         bar: BarData = self.bars.get(tick.vt_symbol)
#         last_tick: TickData = self.last_ticks.get(tick.vt_symbol)
#         period_count: int = self.period_counts.get(tick.vt_symbol, 0)
        
#         if not bar:
#             self.bars[tick.vt_symbol] = BarData(
#                 gateway_name = tick.gateway_name,
#                 symbol = tick.symbol,
#                 exchange = tick.exchange,
#                 datetime = tick.datetime,
#                 interval = Interval.MINUTE,
#                 open_interest = tick.open_interest,
#                 open_price = tick.last_price,
#                 high_price = tick.last_price,
#                 low_price = tick.last_price,
#                 close_price = tick.low_price
#             )

#         else:
#             bar.datetime = tick.datetime
#             bar.close_price = tick.last_price
#             bar.open_interest = tick.open_interest

#             bar.high_price = max(tick.high_price, bar.high_price)
#             bar.low_price = min(tick.low_price, bar.low_price)
            
#             if last_tick:
#                 bar.volume += max(tick.volume - last_tick.volume, 0)
#                 bar.turnover += max(tick.turnover - last_tick.turnover, 0)

#             if bar.datetime.minute != last_tick.datetime.minute:
#                 period_count += 1
                
#                 if self.period == period_count:
#                     bar.datetime.replace(second=0, microsecond=0)
#                     self.on_bar(bar)

#                     self.bars.pop(tick.vt_symbol)
#                     period_count = 0

#                 self.period_counts[tick.vt_symbol] = period_count

#         self.last_ticks[tick.vt_symbol] = tick
