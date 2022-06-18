import asyncio, math
from typing import List
from pandas import DataFrame

from engine import  MainEngine, DataEngine
from config import SNIPER_SETTING
from constant import OrderMode
from object import OrderAsking

class SniperAlgo():
    def __init__(self, ma_engine: MainEngine, gateway_name: str, order_asking: OrderAsking) -> None:
        self.ma_engine: MainEngine = ma_engine
        self.gateway_name: str = gateway_name
        self.order_asking: OrderAsking = order_asking
        
        self.limit: int = SNIPER_SETTING.get("LIMIT", 5)
        self.hit: int = SNIPER_SETTING.get("HIT", 2)
        self.interval: int = SNIPER_SETTING.get("INTERVAL", 10)

        self.vt_orderids: List[str] = []
        self.traded_volume: float = 0

    async def run(self) -> None:
        while self.traded_volume < self.order_asking.volume:
            self.send_order()
            if self.is_force_quit(): break
            await asyncio.sleep(self.interval)

            self.cancel_active_orders()
            await asyncio.sleep(1)
            self.update_traded_volume()
            self.ma_engine.log(f"Traded {self.order_asking.vt_symbol} {self.order_asking.order_mode.value} {self.traded_volume}", self.gateway_name)
            
            self.backup()
            
    def send_order(self) -> List[str]:
        volume = self.get_volume()
        if self.order_asking.order_mode == OrderMode.BUY:
            self.vt_orderids = self.ma_engine.buy(self.order_asking.vt_symbol, volume, self.gateway_name)
        elif self.order_asking.order_mode == OrderMode.SELL:
            self.vt_orderids = self.ma_engine.sell(self.order_asking.vt_symbol, volume, self.gateway_name)
        elif self.order_asking.order_mode == OrderMode.SHORT:
            self.vt_orderids = self.ma_engine.short(self.order_asking.vt_symbol, volume, self.gateway_name)
        elif self.order_asking.order_mode == OrderMode.COVER:
            self.vt_orderids = self.ma_engine.cover(self.order_asking.vt_symbol, volume, self.gateway_name)
        
    def is_force_quit(self) -> bool:
        if not self.vt_orderids:
            self.limit -= 1
            
        if self.limit <= 0:
            return True
        return False

    def cancel_active_orders(self) -> None:
        for vt_orderid in self.vt_orderids:
            self.ma_engine.cancel_active_order(vt_orderid)

    def update_traded_volume(self) -> None:
        for vt_orderid in self.vt_orderids:
            order = self.ma_engine.get_order(vt_orderid)
            if order:
                self.traded_volume += order.traded

    def get_volume(self) -> float:
        tick = self.ma_engine.get_tick(self.order_asking.vt_symbol)
        if tick:
            volume = min(math.ceil(tick.ask_volume_1 / self.hit), self.order_asking.volume - self.traded_volume) \
                if self.order_asking.order_mode in [OrderMode.BUY, OrderMode.COVER] \
                else min(math.ceil(tick.bid_volume_1 / self.hit), self.order_asking.volume - self.traded_volume)
        else:
            volume = min(self.order_asking.volume - self.traded_volume, 1.0)
        return volume

    def backup(self):
        data_engine: DataEngine = self.ma_engine.get_engine(DataEngine.__name__)
        if data_engine is None:
            return

        data: DataFrame = data_engine.get_data(self.gateway_name)
        left_volume = self.order_asking.volume - self.traded_volume

        idx = data.loc[
            (data["ContractID"] == self.order_asking.ContractID) &
            (data["Op1"] == self.order_asking.Op1) &
            (data["Op2"] == self.order_asking.Op2)
        ].index.values[0]

        data.loc[idx, "Num"] = left_volume

        data_engine.backup_data(self.gateway_name)