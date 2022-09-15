
from abc import ABC, abstractmethod
from typing import Any, List

from vnpy.trader.object import BarData, OrderData, TickData, TradeData


class StrategyTemplate(ABC):
    """
    
    """
    def __init__(self, ctp_engine: Any, name: str) -> None:
        super().__init__()

        self.name: str = name

        self.inited: bool = False
        self.trading: bool = False

        self.ctp_engine = ctp_engine

    @abstractmethod
    def on_init(self) -> None:
        """
        Callback when strategy is inited.
        """
        pass

    @abstractmethod
    def on_start(self) -> None:
        """
        Callback when strategy is started.
        """
        pass

    @abstractmethod
    def on_stop(self) -> None:
        """
        Callback when strategy is stopped.
        """
        pass

    @abstractmethod
    def on_tick(self, tick: TickData) -> None:
        """
        Callback of new tick data update.
        """
        pass

    @abstractmethod
    def on_bar(self, bar: BarData) -> None:
        """
        Callback of new bar data update.
        """
        pass

    @abstractmethod
    def on_trade(self, trade: TradeData) -> None:
        """
        Callback of new trade data update.
        """
        pass

    @abstractmethod
    def on_order(self, order: OrderData) -> None:
        """
        Callback of new order data update .
        """
        pass

    def buy(
        self, 
        gateway_name: str, 
        symbol: str, 
        volume: float, 
        is_taker: bool = True, 
        price: float = 0
    ) -> List[str]:
        """
        ## Send buy order to open a long position to a specific gateway.
        """
        return self.ctp_engine.buy(gateway_name, symbol, volume, is_taker, price)

    def sell(
        self, 
        gateway_name: str, 
        symbol: str, 
        volume: float, 
        is_taker: bool = True, 
        price: float = 0
    ) -> List[str]:
        """
        ## Send sell order to close a long position to a specific gateway.
        """
        return self.ctp_engine.sell(gateway_name, symbol, volume, is_taker, price)

    def short(
        self, 
        gateway_name: str, 
        symbol: str, 
        volume: float, 
        is_taker: bool = True, 
        price: float = 0
    ) -> List[str]:
        """
        ## Send short order to open as short position to a specific gateway.
        """
        return self.ctp_engine.short(gateway_name, symbol, volume, is_taker, price)

    def cover(
        self, 
        gateway_name: str, 
        symbol: str, 
        volume: float, 
        is_taker: bool = True, 
        price: float = 0
    ) -> List[str]:
        """
        ## Send cover order to close a short position to a specific gateway.
        """
        return self.ctp_engine.cover(gateway_name, symbol, volume, is_taker, price)