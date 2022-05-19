from datetime import datetime
from functools import lru_cache
from typing import Dict, List
from vnpy.trader.object import(
    BaseData,
    BarData,
    TickData
)

from constant import BacktestingMode

class BacktestingEngine:
    def __init__(self, setting: Dict[str, str]) -> None:
        self.vt_symbols: List[str] = []
        self.mode: BacktestingMode = BacktestingMode.BAR
        self.history_data: List[BaseData] = []

    def load_data(self) -> None:
        if not self.end:
            self.end = datetime.now()

        if self.start >= self.end:
            return

        self.history_data.clear()

        if self.mode == BacktestingMode.BAR:
            data: List[BarData] = self._load_bar_data()
        else:
            data: List[TickData] = self._load_tick_data()

    @lru_cache
    def _load_bar_data(self) -> List[BarData]:
        pass

    @lru_cache
    def _load_tick_data(self) -> List[TickData]:
        pass
    
    def run_backtesting(self) -> None:
        pass
    
    
