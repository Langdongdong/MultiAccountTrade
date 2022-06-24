import logging, pathlib, pandas, time, re

from copy import copy
from datetime import datetime
from abc import ABC
from typing import Any, Callable, Dict, List, Optional, Set
from base.object import BarData

from utility import get_df
from setting import settings

from vnpy.event import Event, EventEngine
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.constant import (
    Offset,
    Direction,
    OrderType,
    Exchange,
)
from vnpy.trader.event import (
    EVENT_LOG,
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_ACCOUNT,
    EVENT_POSITION,
    EVENT_CONTRACT,
)
from vnpy.trader.object import (
    LogData,
    TickData,
    TradeData,
    OrderData,
    AccountData,
    ContractData,
    PositionData,
    OrderRequest,
    SubscribeRequest,
    CancelRequest
)

"""
####################### Change PositionData Struct ######################
"""
class MainEngine():
    """
    Only use for CTP like api.
    """
    def __init__(self, configs: Dict[str, Any]) -> None:
        self.configs = configs

        self.ticks: Dict[str, TickData] = {}
        self.orders: Dict[str, OrderData] = {}
        self.trades: Dict[str, TradeData] = {}
        self.accounts: Dict[str, AccountData] = {}
        self.contracts: Dict[str, ContractData] = {}
        self.positions: Dict[str, PositionData] = {}
        self.active_orders: Dict[str, OrderData] = {}

        self.event_engine = EventEngine()
        self._register_process_event()
        self.event_engine.start()

        self.engines: Dict[str, BaseEngine] = {}
        self.add_engine(LogEngine)

        self.gateways: Dict[str, BaseGateway] = {}
        self._add_gateways()

        self.log("Engine inited")
    
    @staticmethod
    def is_trading_time() -> bool:
        if MainEngine.is_day_trading_time or MainEngine.is_night_trading_time:
            return True
        return False

    @staticmethod
    def is_day_trading_time() -> bool:
        current_time = datetime.now().time()
        if settings.get("trading_time.day_start") <= current_time <= settings.get("trading_time.day_end"):
            return True
        return False

    @staticmethod
    def is_night_trading_time() -> bool:
        current_time = datetime.now().time()
        if settings.get("trading_time.night_start") <= current_time or settings.get("trading_time.night_end") >= current_time:
            return True
        return False

    @staticmethod
    def filter_am_symbol(vt_symbols: Set[str]) -> Set[str]:
        return {vt_symbol for vt_symbol in vt_symbols if re.match("[^0-9]*", vt_symbol, re.I).group().upper() not in settings.get("symbol.day")}
    
    @staticmethod
    def filer_pm_symbol(vt_symbols: Set[str]) -> Set[str]:
        return {vt_symbol for vt_symbol in vt_symbols if re.match("[^0-9]*", vt_symbol, re.I).group().upper() in settings.get("symbol.day")}

    def add_engine(self, engine_class: Any) -> "BaseEngine":
        engine: BaseEngine = engine_class(self, self.event_engine)
        self.engines[engine_class.__name__] = engine
        return engine

    def _add_gateway(self, gateway_name: str, gateway_class: BaseGateway) -> None:
        if gateway_class:
            gateway: BaseGateway = gateway_class(self.event_engine, gateway_name)
            self.gateways[gateway.gateway_name] = gateway

    def _add_gateways(self) -> None:
        accounts: Dict[str, Any] = self.configs.get("accounts")
        for name, config in accounts.items():
            self._add_gateway(name, config.get("gateway"))

    def _connect(self, config: Dict[str, str], gateway_name: str) -> None:
        gateway: Optional[BaseGateway] = self.get_gateway(gateway_name)
        if gateway:
            gateway.connect(config)
        
    def _subscribe(self, req: SubscribeRequest, gateway_name: str) -> None:
        gateway: Optional[BaseGateway] = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)

    def _send_order(self, req: OrderRequest, gateway_name: str) -> str:
        gateway: Optional[BaseGateway] = self.get_gateway(gateway_name)
        if gateway:
            self.log(f"Order {req.vt_symbol} {req.direction.value} {req.offset.value} {req.volume}", gateway_name)
            return gateway.send_order(req)

    def _send_taker_order(self, vt_symbol: str, volume: float, direction: Direction, offset: Offset, gateway_name: str) -> List[str]:
        reqs: List[OrderRequest] = []
        vt_orderids: List[str] = []
        
        tick: Optional[TickData] = self.get_tick(vt_symbol)
        contract: Optional[ContractData] = self.get_contract(vt_symbol)

        if tick is None or contract is None:
            vt_orderids.append("")
            self.log(f"{vt_symbol} tick or contract data is None", gateway_name)
            return vt_orderids

        price: float = tick.ask_price_1 + contract.pricetick * 2 \
            if direction == Direction.LONG \
            else tick.bid_price_1 - contract.pricetick * 2

        req = OrderRequest(
            symbol = contract.symbol,
            exchange = contract.exchange,
            price = price,
            volume = volume,
            direction = direction,
            offset = offset,
            type = OrderType.LIMIT
        )

        if offset == Offset.CLOSE:
            position: Optional[PositionData] = self.get_position(f"{gateway_name}.{contract.vt_symbol}.{Direction.SHORT.value}") \
                if direction == Direction.LONG \
                else self.get_position(f"{gateway_name}.{contract.vt_symbol}.{Direction.LONG.value}")

            if position is None:
                vt_orderids.append("")
                self.log(f"{vt_symbol} {direction.value} position data is None", gateway_name)
                return vt_orderids
            elif position.volume - position.frozen < volume:
                vt_orderids.append("")
                self.log(f"{vt_symbol} {direction.value} {offset.value} {volume} no enough position volume to close", gateway_name, logging.ERROR)
                return vt_orderids

            if contract.exchange in [Exchange.SHFE, Exchange.INE]:
                if not position.yd_volume:
                    req.offset = Offset.CLOSETODAY
                elif position.yd_volume >= req.volume:
                    req.offset = Offset.CLOSEYESTERDAY
                else:
                    req.volume = position.yd_volume
                    req.offset = Offset.CLOSEYESTERDAY

                    req_td = copy(req)
                    req_td.volume = volume - req.volume
                    req_td.offset = Offset.CLOSETODAY
                    reqs.append(req_td)

        reqs.append(req)

        for req in reqs:
            vt_orderids.append(self._send_order(req, gateway_name))

        return vt_orderids

    def _cancel_order(self, req: CancelRequest, gateway_name:str) -> None:
        gateway: Optional[BaseGateway] = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)
    
    def _process_tick_event(self, event: Event) -> None:
        tick: TickData = event.data
        self.ticks[tick.vt_symbol] = tick

    def _process_order_event(self, event: Event) -> None:
        order: OrderData = event.data
        self.orders[order.vt_orderid] = order

        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

    def _process_trade_event(self, event: Event) -> None:
        trade: TradeData = event.data
        self.trades[trade.vt_tradeid] = trade

    def _process_position_event(self, event: Event) -> None:
        position: PositionData = event.data
        self.positions[position.vt_positionid] = position

    def _process_contract_event(self, event: Event) -> None:
        contract: ContractData = event.data
        if self.get_contract(contract.vt_symbol) is None:
            self.contracts[contract.vt_symbol] = contract

    def _process_account_event(self, event: Event) -> None:
        account: AccountData = event.data
        self.accounts[account.gateway_name] = account

    def _register_process_event(self) -> None:
        self.event_engine.register(EVENT_TICK, self._process_tick_event)
        self.event_engine.register(EVENT_ORDER, self._process_order_event)
        self.event_engine.register(EVENT_TRADE, self._process_trade_event)
        self.event_engine.register(EVENT_ACCOUNT, self._process_account_event)
        self.event_engine.register(EVENT_CONTRACT, self._process_contract_event)
        self.event_engine.register(EVENT_POSITION, self._process_position_event)

    def get_gateway(self, gateway_name: str) -> Optional[BaseGateway]:
        return self.gateways.get(gateway_name)

    def get_engine(self, engine_class_name: str) -> Optional["BaseEngine"]:
        return self.engines.get(engine_class_name)

    def get_tick(self, vt_symbol: str, use_df: bool = False) -> Optional[TickData]:
        return get_df(self.ticks.get(vt_symbol), use_df)

    def get_order(self, vt_orderid: str, use_df: bool = False) -> Optional[OrderData]:
        return get_df(self.orders.get(vt_orderid), use_df)

    def get_active_order(self, vt_orderid: str, use_df: bool = False) -> Optional[OrderData]:
        return get_df(self.active_orders.get(vt_orderid), use_df)

    def get_trade(self, vt_tradeid: str, use_df: bool = False) -> Optional[TradeData]:
        return get_df(self.trades.get(vt_tradeid), use_df)

    def get_position(self, vt_positionid: str, use_df: bool = False) -> Optional[PositionData]:
        return get_df(self.positions.get(vt_positionid), use_df)

    def get_contract(self, vt_symbol: str, use_df: bool = False) -> Optional[ContractData]:
        return get_df(self.contracts.get(vt_symbol), use_df)

    def get_account(self, gateway_name: str) -> Optional[AccountData]:
        return self.accounts.get(gateway_name)

    def get_all_gateways(self) -> List[BaseGateway]:
        return list(self.gateways.values())

    def get_all_gateway_names(self) -> List[str]:
        return list(self.gateways.keys())

    def get_all_ticks(self, use_df: bool = False) -> List[TickData]:
        return get_df(list(self.ticks.values()), use_df)

    def get_all_orders(self, use_df: bool = False) -> List[OrderData]:
        return get_df(list(self.orders.values()), use_df)

    def get_all_active_orders(self, use_df: bool = False) -> List[OrderData]:
        return get_df(list(self.active_orders.values()), use_df)

    def get_all_trades(self, use_df: bool = False) -> List[TradeData]:
        return get_df(list(self.trades.values()), use_df)

    def get_all_positions(self, use_df: bool = False) -> List[PositionData]:
        return get_df(list(self.positions.values()), use_df)

    def get_all_contracts(self, use_df: bool = False) -> List[ContractData]:
        return get_df(list(self.contracts.values()), use_df)

    def get_all_accounts(self, use_df: bool = False) -> List[AccountData]:
        return get_df(list(self.accounts.values()), use_df) 

    def get_gateway_positions(self, gateway_name: str, use_df: bool = False) -> List[PositionData]:
        return get_df([position for position in self.get_all_positions() if position.gateway_name == gateway_name], use_df)

    def is_gateway_inited(self, gateway_name: str) -> bool:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.td_api.contract_inited
        return False

    def connect(self) -> None:
        accounts: Dict[str, Any] = self.configs.get("accounts")
        for gateway_name, config in accounts.items():
            self._connect(config, gateway_name)
        
        while True:
            time.sleep(3)
            not_inited_gateway_names = [gateway_name for gateway_name in self.get_all_gateway_names() if not self.is_gateway_inited(gateway_name)]
            if not not_inited_gateway_names:
                break

        self.log("Connected")
        
    def susbcribe(self, vt_symbols: Set[str]) -> None:
        for vt_symbol in vt_symbols:
            contract = self.get_contract(vt_symbol)
            if contract:
                req = SubscribeRequest(
                    symbol = contract.symbol,
                    exchange = contract.exchange
                )
                self._subscribe(req, self.get_all_gateway_names()[0])

        time.sleep(3)
        self.log(f"Subscribed") 
        
    def buy(self, vt_symbol: str, volume: float, gateway_name: str) -> List[str]:
        return self._send_taker_order(vt_symbol, volume, Direction.LONG, Offset.OPEN, gateway_name)
    
    def sell(self, vt_symbol: str, volume: float, gateway_name: str) -> List[str]:
        return self._send_taker_order(vt_symbol, volume, Direction.SHORT, Offset.CLOSE, gateway_name)

    def short(self, vt_symbol: str, volume: float, gateway_name: str) -> List[str]:
        return self._send_taker_order(vt_symbol, volume, Direction.SHORT, Offset.OPEN, gateway_name)

    def cover(self, vt_symbol: str, volume: float, gateway_name: str) -> List[str]:
        return self._send_taker_order(vt_symbol, volume, Direction.LONG, Offset.CLOSE, gateway_name)

    def cancel_active_order(self, vt_orderid: str) -> None:
        active_order = self.get_active_order(vt_orderid)
        if active_order:
            req = active_order.create_cancel_request()
            self._cancel_order(req, active_order.gateway_name)
            self.log(f"Cancel {active_order.vt_symbol} {active_order.direction.value} {active_order.offset.value} {active_order.volume - active_order.traded}", 
            active_order.gateway_name)

    def log(self, msg: str, gateway_name: str = "", level: int = logging.INFO) -> None:
        log = LogData(gateway_name, msg, level)
        event = Event(EVENT_LOG, log)
        self.event_engine.put(event)

    def close(self) -> None:
        self.event_engine.stop()

        for engine in self.engines.values():
            engine.close()

        for gateway in self.gateways.values():
            gateway.close()

        self.log("Engine closed")


class BaseEngine(ABC):
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
    
    def close(self):
        pass


class DataEngine(BaseEngine):
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        super().__init__(main_engine, event_engine)

        self.datas: Dict[str, pandas.DataFrame]  = {}
        
        self.load_file_paths: Dict[str, str] = {}
        self.backup_file_paths: Dict[str, str] = {}

        self._add_load_dir_path()
        self._add_backup_dir_path()

    def _add_load_dir_path(self) -> None:
        try:
            self.load_dir_path = pathlib.Path(FILE_SETTING.get("LOAD_DIR_PATH"))
            if not self.load_dir_path.exists():
                self.load_dir_path.mkdir()
        except:
            self.main_engine.log("Order directory path cause error", level=logging.ERROR)

    def _add_backup_dir_path(self) -> None:
        try:
            self.backup_dir_path = pathlib.Path(FILE_SETTING.get("BACKUP_DIR_PATH"))
            if not self.backup_dir_path.exists():
                self.backup_dir_path.mkdir()
        except:
            self.main_engine.log("Backup directory path cause error", level=logging.ERROR)

    def get_load_dir_path(self) -> pathlib.Path:
        return self.load_dir_path

    def get_backup_dir_path(self) -> pathlib.Path:
        return self.backup_dir_path
    
    def add_load_file_path(self, gateway_name: str, file_name: str) -> pathlib.Path:
        load_file_path: pathlib.Path = self.load_dir_path.joinpath(file_name)
        self.load_file_paths[gateway_name] = load_file_path
        return load_file_path

    def get_load_file_path(self, gateway_name: str) -> Optional[pathlib.Path]:
        return self.load_file_paths.get(gateway_name)

    def delete_load_file(self, gateway_name: str) -> None:
        file_path: Optional[pathlib.Path] = self.get_load_file_path(gateway_name)
        if file_path.exists():
            file_path.unlink()

    def add_backup_file_path(self, gateway_name: str, file_name: str) -> pathlib.Path:
        backup_file_path: pathlib.Path = self.backup_dir_path.joinpath(file_name)
        self.backup_file_paths[gateway_name] = backup_file_path
        return backup_file_path
    
    def get_backup_file_path(self, gateway_name: str) -> Optional[pathlib.Path]:
        return self.backup_file_paths.get(gateway_name)

    def delete_backup_file(self, gateway_name: str) -> None:
        file_path: Optional[pathlib.Path] = self.get_backup_file_path(gateway_name)
        if file_path.exists():
            file_path.unlink()

    def add_data(self, gateway_name: str, data: pandas.DataFrame) -> None:
        self.datas[gateway_name] = data

    def get_data(self, gateway_name: str) -> Optional[pandas.DataFrame]:
        return self.datas.get(gateway_name)

    def load_data(self, gateway_name: str, file_name: str, cache: bool = False) -> Optional[pandas.DataFrame]:
        try:
            file_path: pathlib.Path = self.add_backup_file_path(gateway_name, f"{file_name}_backup.csv")
            if not file_path.exists():
                file_path: pathlib.Path = self.add_load_file_path(gateway_name, file_name)
                if not file_path.exists():
                    self.main_engine.log("Load file path does not exist", gateway_name)
                    return
        except:
            self.main_engine.log("Backup or load file path cause error", gateway_name, logging.ERROR)
            return

        data = pandas.read_csv(file_path)
        self.add_data(gateway_name, data)

        if file_path is not self.get_backup_file_path(gateway_name):
            self.backup_data(gateway_name)

        self.main_engine.log("Data loaded", gateway_name)
        return data
        
    def delete_data(self, gateway_name: str) -> None:
        self.datas.pop(gateway_name, None)

    def backup_data(self, gateway_name: str) -> None:
        data: Optional[pandas.DataFrame] = self.get_data(gateway_name)
        if data is not None:
            file_path = self.get_backup_file_path(gateway_name)
            if file_path:
                data.to_csv(file_path, index=False)
            else:
                self.main_engine.log(f"Backup file path is None", gateway_name)
        else:
            self.main_engine.log(f"Backup data is None", gateway_name)


class LogEngine(BaseEngine):
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        super().__init__(main_engine, event_engine)

        self.logger: logging.Logger = logging.getLogger("MainEngine")
        self.formatter: logging.Formatter = logging.Formatter("%(asctime)s  %(levelname)s: %(message)s")
        self.logger.setLevel(logging.INFO)
        
        self._add_log_dir_path()

        self._add_file_handler()
        self._add_console_handler()

        self._register_event()
    
    def _add_log_dir_path(self) -> None:
        try:
            self.log_dir_path: pathlib.Path = pathlib.Path(settings.get("log.dir"))
            if not self.log_dir_path.exists():
                self.log_dir_path.mkdir()
        except:
            self.main_engine.log("Log directory path cause error.", level=logging.ERROR)

    def _add_file_handler(self) -> None:
        file_name: str = f"{datetime.now().strftime('%Y%m%d')}.log"
        file_path: pathlib.Path = self.log_dir_path.joinpath(file_name)

        try:
            file_handler: logging.FileHandler = logging.FileHandler(file_path, mode="a", encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)
        except:
            self.main_engine.log("Log file path cause error", level=logging.ERROR)


    def _add_console_handler(self) -> None:
        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.formatter)

        self.logger.addHandler(console_handler)

    def _process_log_event(self, event: Event) -> None:
        log: LogData = event.data
        self.logger.log(log.level, f"{log.gateway_name} {log.msg}")

    def _register_event(self) -> None:
        self.event_engine.register(EVENT_LOG, self._process_log_event)


class BarEngine(BaseEngine):
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        super().__init__(main_engine, event_engine)

        self.bars: Dict[str, BarData] = {}
        self.last_ticks: Dict[str, TickData] = {}
        self.period_counts: Dict[str, int] = {}

    def init(self, period: int, on_bar: Callable) -> None:
        self.period: int = period
        self.on_bar: Callable = on_bar

        self.event_engine.register(EVENT_TICK, self._process_tick_event)

    def _process_tick_event(self, event: Event):
        tick: TickData = event.data
        self.update_minute_bar(tick)

    def update_minute_bar(self, tick: TickData) -> None:
        bar: BarData = self.bars.get(tick.vt_symbol)
        last_tick: TickData = self.last_ticks.get(tick.vt_symbol)
        period_count: int = self.period_counts.get(tick.vt_symbol, 0)
        
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

            bar.high = max(tick.high_price, bar.high)
            bar.low = min(tick.low_price, bar.low)

            if last_tick:
                bar.volume += max(tick.volume - last_tick.volume, 0)
                bar.money += max(tick.turnover - last_tick.turnover, 0)

            if bar.date.minute != last_tick.datetime.minute:
                period_count += 1
                
                if self.period == period_count:
                    bar.date.replace(second=0, microsecond=0)
                    self.on_bar(bar)

                    self.bars.pop(tick.vt_symbol)
                    period_count = 0

                self.period_counts[tick.vt_symbol] = period_count

        self.last_ticks[tick.vt_symbol] = tick
