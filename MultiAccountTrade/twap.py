import asyncio, math
from typing import Any, List, Dict

from pandas import DataFrame

from engine import BackupEngine, MAEngine
from constant import OrderMode, OrderRequest

from vnpy.trader.object import TradeData

class TWAP():
    def __init__(self, engine: MAEngine, gateway_name: str, request: OrderRequest, setting: Dict[str, int] = None) -> None:
        self.engine: MAEngine = engine
        self.gateway_name: str = gateway_name

        self.vt_symbol: str = request.vt_symbol
        self.order_mode: OrderMode = request.order_mode
        self.volume: float = request.volume
        
        self.time: int = setting.get("TIME")
        self.interval: int = setting.get("INTERVAL")

        self.vt_orderids: List[str] = []
        self.traded_volume: float = 0
        self.twap_volume: float = self.get_twap_volume()

    async def run(self) -> None:
        while self.traded_volume < self.volume:
            self.send_order()
            await asyncio.sleep(self.interval)
            self.cancel_active_orders()
            await asyncio.sleep(1)
            self.update_traded_volume()
            backup(
                self.engine,
                self.gateway_name,
                self.vt_symbol,
                self.order_mode,
                self.volume - self.traded_volume
                )
            
    def send_order(self) -> List[str]:
        volume = min(self.twap_volume, self.volume - self.traded_volume)

        if self.order_mode == OrderMode.BUY:
            self.vt_orderids = self.engine.buy(self.vt_symbol, volume, self.gateway_name)
        elif self.order_mode == OrderMode.SELL:
            self.vt_orderids = self.engine.sell(self.vt_symbol, volume, self.gateway_name)
        elif self.order_mode == OrderMode.SHORT:
            self.vt_orderids = self.engine.short(self.vt_symbol, volume, self.gateway_name)
        elif self.order_mode == OrderMode.COVER:
            self.vt_orderids = self.engine.cover(self.vt_symbol, volume, self.gateway_name)

    def cancel_active_orders(self) -> None:
        for vt_orderid in self.vt_orderids:
            self.engine.cancel_active_order(vt_orderid)

    def update_traded_volume(self) -> None:
        trades: List[TradeData] = self.engine.get_all_trades()
        for trade in trades:
            if trade.orderid in self.vt_orderids:
                self.traded_volume += trade.volume

    def get_twap_volume(self) -> float:
        return max(float(math.floor(self.volume / (self.time / self.interval))), 1.0)


def backup(engine: MAEngine, gateway_name: str, vt_symbol: str, order_mode: OrderMode, left_volume: float):
    backup_engine: BackupEngine = engine.backup_engine
    data: DataFrame = backup_engine.get_backup_data(gateway_name)

    symbol: str = OrderRequest.convert_to_symbol(vt_symbol)
    Op1, Op2 = OrderRequest.convert_to_order_mode(order_mode)

    idx = data.loc[
        (data["ContractID"] == symbol) &
        (data["Op1"] == Op1) &
        (data["Op2"] == Op2)
    ].index.values[0]
    data.loc[idx, "Num"] = left_volume

    backup_engine.backup(gateway_name)