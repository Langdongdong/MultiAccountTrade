
from concurrent.futures import Future, ThreadPoolExecutor
import logging
import traceback

from abc import ABC
from copy import copy
from datetime import datetime, timedelta
from mimetypes import inited
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Type

from base.database import MongoDatabase
from base.setting import SETTINGS

from vnpy.event import Event, EventEngine
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.utility import BarGenerator
from vnpy.trader.constant import Status

from vnpy.trader.constant import (
    Direction,
    Exchange,
    Offset,
    OrderType,
)

from vnpy.trader.event import (
    EVENT_LOG,
    EVENT_TICK,
    EVENT_TIMER,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_ACCOUNT,
    EVENT_POSITION,
    EVENT_CONTRACT,
)

from vnpy.trader.object import (
    BarData,
    LogData,
    TickData,
    TradeData,
    OrderData,
    AccountData,
    ContractData,
    PositionData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
)

from strategy.template import StrategyTemplate

EVENT_BAR = "eBar"

class CtpEngine():
    """
    #  Used for ctp-like gateways.

    ## Note:

    ## 1. PositionData add attribute 'self.positionid: str = f"{self.gateway_name}.{self.symbol}.{self.direction.value}"'.

    ## 2. BarData add attribute "limit_up", "limit_down", "avg_price", "pre_close".

    ## 3. BarGenerator's "update_tick()" add "limit_up", "limit_down", "pre_close".

    ## 4. Porcess_bar_event add bar.avg_prive calculation.
    """

    @staticmethod
    def is_trading_time() -> bool:
        if CtpEngine.is_day_trading_time() or CtpEngine.is_night_trading_time():
            return True
        return False

    @staticmethod
    def is_day_trading_time() -> bool:
        now = datetime.now().time()
        trading_time = SETTINGS.get("tradingtime.day")

        if trading_time[0] <= now <= trading_time[1]:
                return True
        return False

    @staticmethod
    def is_night_trading_time() -> bool:
        now = datetime.now().time()
        trading_time = SETTINGS.get("tradingtime.night")

        if trading_time[0] <= now or trading_time[1] >= now:
            return True

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.event_engine = EventEngine()
        self.event_engine.start()

        self.engines: Dict[str, BaseEngine] = {}

        self.exchanges: List[Exchange] = []
        self.gateways: Dict[str, BaseGateway] = {}

        self.ticks: Dict[str, TickData] = {}
        self.bars: Dict[str, BarData] = {}
        self.orders: Dict[str, OrderData] = {}
        self.trades: Dict[str, TradeData] = {}
        self.accounts: Dict[str, AccountData] = {}
        self.contracts: Dict[str, ContractData] = {}
        self.positions: Dict[str, PositionData] = {}
        self.active_orders: Dict[str, OrderData] = {}

        self.bar_generators: Dict[str, BarGenerator] = {}
        self.database: MongoDatabase = MongoDatabase()

        self.thread_pool_executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1)
        self.strategies: Dict[str, Type[StrategyTemplate]] = {}
        self.orderid_strategy_map: Dict[str, Type[StrategyTemplate]] = {}

        self.register_event()
        self.init_engines()

    def add_engine(self, engine_class: Any) -> "BaseEngine":
        """
        ## Add function engine.
        """
        engine: BaseEngine = engine_class(self, self.event_engine)
        self.engines[engine.engine_name] = engine
        return engine

    def init_engines(self) -> None:
        """
        ## Init basic engines.
        """
        self.add_engine(LogEngine)

    def add_gateway(self, gateway_class: Type[BaseGateway], gateway_name: str) -> BaseGateway:
        """
        ## Add gateway.
        """
        gateway: BaseGateway = gateway_class(self.event_engine, gateway_name)
        self.gateways[gateway_name] = gateway

        # Add gateway supported exchanges into engine
        for exchange in gateway.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return gateway

    def write_log(self, msg: str, source: str = "") -> None:
        """
        ## Put log event with specific message.
        """
        log: LogData = LogData(msg=msg, gateway_name=source)
        event: Event = Event(EVENT_LOG, log)
        self.event_engine.put(event)

    def get_gateway(self, gateway_name: str) -> BaseGateway:
        """
        ## Return gateway object by name.
        """
        gateway: BaseGateway = self.gateways.get(gateway_name, None)
        if not gateway:
            self.write_log(f"Cannot get the gateway: {gateway_name}")
        return gateway

    def get_engine(self, engine_name: str) -> "BaseEngine":
        """
        ## Return engine object by name.
        """
        engine: BaseEngine = self.engines.get(engine_name, None)
        if not engine:
            self.write_log(f"Cannot get the engine: {engine_name}")
        return engine

    def get_gateway_default_setting(self, gateway_name: str) -> Optional[Dict[str, Any]]:
        """
        ## Get default setting dict of a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.get_default_setting()
        return None

    def get_all_gateway_names(self) -> List[str]:
        """
        ## Get all names of gateways added in main engine.
        """
        return list(self.gateways.keys())

    def get_all_exchanges(self) -> List[Exchange]:
        """
        ## Get all exchanges.
        """
        return self.exchanges

    def is_connected(self, gateway_name) -> bool:
        """
        ## Check connection status of a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.td_api.contract_inited

    def is_all_connected(self) -> bool:
        """
        ## Check connection status of all gateways.
        """
        for gateway_name in self.get_all_gateway_names():
            if not self.is_connected(gateway_name):
                return False
        return True

    def connect(self, setting: dict, gateway_name: str) -> None:
        """
        ## Start connection of a specific gateway.
        """
        gateway: BaseGateway = self.add_gateway(setting["gateway"], gateway_name)
        if gateway:
            gateway.connect(setting)

    def connect_all(self, settings: dict) -> None:
        """
        ## Start connection of all gateways.
        """
        for gateway_name, setting in settings.items():
            self.connect(setting, gateway_name)

        while True:
            if self.is_all_connected():
                break

    def subscribe(self, symbols: Sequence[str], gateway_name: str = "") -> None:
        """
        ## Subscribe tick data update of a specific gateway.
        """
        if not gateway_name:
            gateway_name = self.get_all_gateway_names()[0]

        gateway = self.get_gateway(gateway_name)
        if gateway:
            for symbol in symbols:
                contract: Optional[ContractData] = self.get_contract(symbol)
                if contract:
                    req = SubscribeRequest(
                        symbol=contract.symbol,
                        exchange=contract.exchange
                    )
                    gateway.subscribe(req)
                
                self.bar_generators[symbol] = BarGenerator(self.callback_generate_bar)

    def send_order(
        self,
        strategy: StrategyTemplate,
        gateway: BaseGateway,
        symbol: str, 
        volume: float, 
        direction: Direction, 
        offset: Offset,
        is_taker: bool,
        price: float,
    ) -> List[str]:
        """
        ## Send new order request to a specific gateway.
        """
        contract: Optional[ContractData] = self.get_contract(symbol)
        if not contract:
            return []

        if is_taker:
            tick: Optional[TickData] = self.get_tick(symbol)
            if not tick:
                return []

            price = tick.ask_price_1 + contract.pricetick * 2 \
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
        reqs = self.convert_order_request(gateway.gateway_name, req)
        if not reqs:
            return []

        orderids: List[str] = []
        for req in reqs:
            orderid = gateway.send_order(req)
            orderids.append(orderid)

            if strategy:
                self.orderid_strategy_map[orderid] = strategy

        return orderids

    def convert_order_request(self, gateway_name: str, req: OrderRequest) -> List[OrderRequest]:
        if req.offset == Offset.CLOSE:
            if req.direction == Direction.LONG:
                pos: Optional[PositionData] = self.get_position(f"{gateway_name}.{req.symbol}.{Direction.SHORT.value}")
            else:
                pos: Optional[PositionData] = self.get_position(f"{gateway_name}.{req.symbol}.{Direction.LONG.value}")
            if not pos:
                return []

            pos_available = pos.volume - pos.frozen
            if req.volume > pos_available:
                return []

            if req.exchange in [Exchange.SHFE, Exchange.INE]:
                td_pos_available = pos_available - pos.yd_volume
                
                if req.volume <= td_pos_available:
                    req_td: OrderRequest = copy(req)
                    req_td.offset = Offset.CLOSETODAY
                    return [req_td]
                else:
                    reqs: List[OrderRequest] = []

                    if td_pos_available > 0:
                        req_td: OrderRequest = copy(req)
                        req_td.offset = Offset.CLOSETODAY
                        req_td.volume = td_pos_available
                        reqs.append(req_td)
                    
                    req_yd: OrderRequest = copy(req)
                    req_yd.offset = Offset.CLOSEYESTERDAY
                    req_yd.volume = req.volume - td_pos_available
                    reqs.append(req_yd)
                    return reqs
                    
        return [req]

    def buy(
        self, 
        gateway: BaseGateway, 
        symbol: str, 
        volume: float, 
        is_taker: bool = True, 
        price: float = 0,
        strategy: StrategyTemplate = None
    ) -> List[str]:
        """
        ## Send buy order to open a long position to a specific gateway.
        """
        return self.send_order(strategy, gateway, symbol, volume, Direction.LONG, Offset.OPEN, is_taker, price)

    def sell(
        self,
        gateway: BaseGateway, 
        symbol: str, 
        volume: float, 
        is_taker: bool = True, 
        price: float = 0,
        strategy: StrategyTemplate = None
    ) -> List[str]:
        """
        ## Send sell order to close a long position to a specific gateway.
        """
        return self.send_order(strategy, gateway, symbol, volume, Direction.SHORT, Offset.CLOSE, is_taker, price)

    def short(
        self,
        gateway: BaseGateway, 
        symbol: str, 
        volume: float, 
        is_taker: bool = True, 
        price: float = 0,
        strategy: StrategyTemplate = None
    ) -> List[str]:
        """
        ## Send short order to open as short position to a specific gateway.
        """
        return self.send_order(strategy, gateway, symbol, volume, Direction.SHORT, Offset.OPEN, is_taker, price)

    def cover(
        self,
        gateway: BaseGateway, 
        symbol: str, 
        volume: float, 
        is_taker: bool = True, 
        price: float = 0,
        strategy: StrategyTemplate = None
    ) -> List[str]:
        """
        ## Send cover order to close a short position to a specific gateway.
        """
        return self.send_order(strategy, gateway, symbol, volume, Direction.LONG, Offset.CLOSE, is_taker, price)

    def cancel_order(self, req: CancelRequest, gateway_name: str) -> None:
        """
        ## Send cancel order request to a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)

    def tick_filter(self, tick: TickData) -> Optional[TickData]:
        """
        ## Filter tick data. Return None if tick.datetime is not in the correct range else return tick data.
        """
        if not SETTINGS["tickfilter.active"]:
            return tick

        now = datetime.now()
        now = now.replace(tzinfo=tick.datetime.tzinfo)

        if (
            tick.datetime > now or 
            tick.datetime < now - timedelta(seconds=SETTINGS["tickfilter.latency"])
        ):
            return

        return tick

    def bar_filter(self, bar: BarData) -> Optional[BarData]:
        """
        ## Filter bar data. Return None if bar.datetime is not in the correct range else return bar data.
        """
        if not SETTINGS["barfilter.active"]:
            return bar

        now = datetime.now()
        now = now.replace(tzinfo=bar.datetime.tzinfo)

        if (
            bar.datetime < now and 
            bar.datetime.minute != now.minute and 
            now.second >= SETTINGS["barfilter.latency"]
        ):
            return

        return bar

    def register_event(self) -> None:
        """
        ## Register events.
        """
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)

        self.event_engine.register(EVENT_BAR, self.process_bar_event)
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)
        
    def callback_generate_bar(self, bar: BarData) -> None:
        """
        ## Process bar event.
        """
        # Add average price attribute to bar data.
        contract: ContractData = self.get_contract(bar.symbol)
        tick: TickData = self.get_tick(bar.symbol)
        if contract and tick and tick.volume:
            bar.avg_price = (tick.turnover / (tick.volume * contract.size))

        # Put bar data to event engine.
        event: Event = Event(EVENT_BAR, bar)
        self.event_engine.put(event)

    def process_timer_event(self, event: Event) -> None:
        """
        ## Process timer event.
        """
        # Force to generate bar data if too late to receive tick data.
        bars = [
            bg.generate() 
            for bg in self.get_all_bar_generators() 
            if bg.bar and not self.bar_filter(bg.bar)
        ]

        # Put bar data to event engine.
        for bar in bars:
            event: Event = Event(EVENT_BAR, bar)
            self.event_engine.put(event)

    def process_tick_event(self, event: Event) -> None:
        """
        ## Process tick event.
        """
        tick: TickData = self.tick_filter(event.data)
        if tick:
            self.ticks[tick.symbol] = tick

            self.process_strategy_tick_event(tick)

            bar_generator: BarGenerator = self.get_bar_generator(tick.symbol)
            if bar_generator:
                bar_generator.update_tick(tick)

    def process_bar_event(self, event: Event) -> None:
        """
        ## Process bar event.
        """
        bar: BarData = event.data
        self.bars[bar.symbol] = bar

        self.process_strategy_bar_event(bar)
        
        # Save bar data to database.
        if SETTINGS["database.active"]:
            self.thread_pool_executor.submit(self.database.save_bar_data, [bar])
            # self.database.save_bar_data([bar])

    def process_order_event(self, event: Event) -> None:
        """
        ## Process order event.
        """
        order: OrderData = event.data
        self.orders[order.orderid] = order

        if order.is_active():
            self.active_orders[order.orderid] = order
        elif order.orderid in self.active_orders:
            self.active_orders.pop(order.orderid)

        self.process_strategy_order_event(order)

    def process_trade_event(self, event: Event) -> None:
        """
        ## Process trade event.
        """
        trade: TradeData = event.data
        self.trades[trade.tradeid] = trade

        self.process_strategy_trade_event(trade)

    def process_position_event(self, event: Event) -> None:
        """
        ## Process position event.
        """
        position: PositionData = event.data
        self.positions[position.positionid] = position

    def process_account_event(self, event: Event) -> None:
        """
        ## Process account event.
        """
        account: AccountData = event.data
        self.accounts[account.accountid] = account

    def process_contract_event(self, event: Event) -> None:
        """
        ## Process contract event.
        """
        contract: ContractData = event.data
        self.contracts[contract.symbol] = contract

    def get_bar_generator(self, symbol: str) -> Optional[BarGenerator]:
        """
        ## Get bar generator by symbol.
        """
        return self.bar_generators.get(symbol, None)

    def get_tick(self, symbol: str) -> Optional[TickData]:
        """
        ## Get latest market tick data by symbol.
        """
        return self.ticks.get(symbol, None)

    def get_order(self, orderid: str) -> Optional[OrderData]:
        """
        ## Get latest order data by orderid.
        """
        return self.orders.get(orderid, None)

    def get_trade(self, tradeid: str) -> Optional[TradeData]:
        """
        ## Get trade data by tradeid.
        """
        return self.trades.get(tradeid, None)

    def get_position(self, positionid: str) -> Optional[PositionData]:
        """
        ## Get latest position data by positionid.
        """
        return self.positions.get(positionid, None)

    def get_account(self, accountid: str) -> Optional[AccountData]:
        """
        ## Get latest account data by accountid.
        """
        return self.accounts.get(accountid, None)

    def get_contract(self, symbol: str) -> Optional[ContractData]:
        """
        ## Get contract data by symbol.
        """
        return self.contracts.get(symbol, None)

    def get_all_bar_generators(self) -> List[BarGenerator]:
        """
        ## Get all bar generator.
        """
        return list(self.bar_generators.values())

    def get_all_ticks(self) -> List[TickData]:
        """
        ## Get all tick data.
        """
        return list(self.ticks.values())

    def get_all_orders(self) -> List[OrderData]:
        """
        ## Get all order data.
        """
        return list(self.orders.values())

    def get_all_trades(self) -> List[TradeData]:
        """
        ## Get all trade data.
        """
        return list(self.trades.values())

    def get_all_positions(self) -> List[PositionData]:
        """
        ## Get all position data.
        """
        return list(self.positions.values())

    def get_all_accounts(self) -> List[AccountData]:
        """
        ## Get all account data.
        """
        return list(self.accounts.values())

    def get_all_contracts(self) -> List[ContractData]:
        """
        ## Get all contract data.
        """
        return list(self.contracts.values())

    def get_all_active_orders(self, symbol: str = "") -> List[OrderData]:
        """
        ## Get all active orders by symbol. If symbol is empty, return all active orders.
        """
        if not symbol:
            return list(self.active_orders.values())
        else:
            active_orders: List[OrderData] = [
                order
                for order in self.active_orders.values()
                if order.symbol == symbol
            ]
            return active_orders

    def close(self) -> None:
        """
        ## Make sure every gateway and app is closed properly before programme exit.
        """
        # Stop event engine first to prevent new timer event.
        self.event_engine.stop()

        for engine in self.engines.values():
            engine.close()

        for gateway in self.gateways.values():
            gateway.close()



    def add_strategy(self, strategy_class: Type[StrategyTemplate], strategy_name: str = "") -> StrategyTemplate:
        """"""
        if not strategy_name:
            strategy_name = strategy_class.__name__

        strategy: StrategyTemplate = strategy_class(self, strategy_name)
        self.strategies[strategy_name] = strategy
        return strategy

    def get_strategy(self, strategy_name: str) -> StrategyTemplate:
        """"""
        return self.strategies.get(strategy_name, None)

    def get_all_strategies(self) -> List[StrategyTemplate]:
        """"""
        return list(self.strategies.values())

    def init_strategy(self, strategy_name: str) -> Future:
        """
        ## Init a strategy.
        """
        return self.thread_pool_executor.submit(self._init_strategy, strategy_name)

    def _init_strategy(self, strategy_name: str) -> None:
        """
        ## Init strategies in queue.
        """
        strategy: StrategyTemplate = self.get_strategy(strategy_name)
        if strategy:

            if strategy.inited:
                self.write_log(f"{strategy_name}已经完成初始化，禁止重复操作")
                return

            self.write_log(f"{strategy_name}开始执行初始化")

            # Call on_init function of strategy
            self.call_strategy_func(strategy, strategy.on_init)

            # # Restore strategy data(variables)
            # data: Optional[dict] = self.strategy_data.get(strategy_name, None)
            # if data:
            #     for name in strategy.variables:
            #         value = data.get(name, None)
            #         if value is not None:
            #             setattr(strategy, name, value)

            # Put event to update init completed status.
            strategy.inited = True
            self.write_log(f"{strategy_name}初始化完成")

    def init_all_strategies(self) -> Dict[str, Future]:
        """
        ## Init all strategies.
        """
        futures: Dict[str, Future] = {}
        for strategy_name in self.strategies.keys():
            futures[strategy_name] = self.init_strategy(strategy_name)
        return futures
    
    def start_strategy(self, strategy_name: str) -> None:
        """
        ## Start a strategy.
        """
        strategy: StrategyTemplate = self.get_strategy(strategy_name)
        if strategy:

            if not strategy.inited:
                self.write_log(f"策略{strategy.name}启动失败，请先初始化")
                return

            if strategy.trading:
                self.write_log(f"{strategy_name}已经启动，请勿重复操作")
                return

            self.call_strategy_func(strategy, strategy.on_start)
            strategy.trading = True

    def start_all_strategies(self) -> None:
        """
        ## Start all strategies.
        """
        for strategy_name in self.strategies.keys():
            self.start_strategy(strategy_name)

    def stop_strategy(self, strategy_name: str) -> None:
        """
        ## Stop a strategy.
        """
        strategy: StrategyTemplate = self.get_strategy(strategy_name)
        if not strategy.trading:
            return

        # Call on_stop function of the strategy
        self.call_strategy_func(strategy, strategy.on_stop)

        # Change trading status of strategy to False
        strategy.trading = False

        # Cancel all orders of the strategy
        for order in strategy.get_all_orders():
            self.cancel_order(order.create_cancel_request(), order.gateway_name)

    def stop_all_strategies(self) -> None:
        """
        ## Stop all strategy.
        """
        for strategy_name in self.strategies.keys():
            self.stop_strategy(strategy_name)

    def call_strategy_func(
        self, strategy: StrategyTemplate, func: Callable, params: Any = None
    ) -> None:
        """
        Call function of a strategy and catch any exception raised.
        """
        try:
            if params:
                func(params)
            else:
                func()
        except Exception:
            strategy.trading = False
            strategy.inited = False

            msg: str = f"触发异常已停止\n{traceback.format_exc()}"
            self.write_log(msg, strategy.name)

    def process_strategy_tick_event(self, tick: TickData):
        strategies: List[StrategyTemplate] = self.get_all_strategies()
        if not strategies:
            return

        for strategy in strategies:
            if strategy.inited:
                self.call_strategy_func(strategy, strategy.on_tick, tick)

    def process_strategy_bar_event(self, bar: BarData) -> None:
        strategies: List[StrategyTemplate] = self.get_all_strategies()
        if not strategies:
            return

        for strategy in strategies:
            if strategy.inited:
                self.call_strategy_func(strategy, strategy.on_bar, bar)

    def process_strategy_order_event(self, order: OrderData) -> None:
        strategy: StrategyTemplate = self.orderid_strategy_map.get(order.orderid, None)
        if not strategy:
            return

        if order.is_active():
            # Update strategy orders dict.
            if not strategy.get_order(order.orderid):
                strategy.orders[order.orderid] = order
        else:
            # Update strategy orders dict.
            strategy.orders.pop(order.orderid)

            # Update orderid_strategy_map dict.
            self.orderid_strategy_map.pop(order.orderid)

        self.call_strategy_func(strategy, strategy.on_order, order)

    def process_strategy_trade_event(self, trade: TradeData) -> None:
        strategy: StrategyTemplate = self.orderid_strategy_map.get(trade.orderid, None)
        if not strategy:
            return
        
        self.call_strategy_func(strategy, strategy.on_trade, trade)


class BaseEngine(ABC):
    def __init__(self, ctp_engine: CtpEngine, evnet_engine: EventEngine, engine_name: str) -> None:
        """"""
        self.ctp_engine: CtpEngine = ctp_engine
        self.event_engine: EventEngine = evnet_engine
        self.engine_name: str = engine_name

    def close(self) -> None:
        """"""
        pass


class LogEngine(BaseEngine):
    """
    # Processes log event and output with logging engine.
    """
    def __init__(self, ctp_engine: CtpEngine, evnet_engine: EventEngine) -> None:
        super().__init__(ctp_engine, evnet_engine, "log")

        if not SETTINGS["log.active"]:
            return

        self.level: int = SETTINGS["log.level"]

        self.logger: logging.Logger = logging.getLogger("ctp_engine")
        self.logger.setLevel(self.level)

        self.formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s: %(message)s"
        )

        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()

        if SETTINGS["log.file"]:
            self.add_file_handler()

        self.register_event()

    def add_null_handler(self) -> None:
        """
        ## Add null handler for logger.
        """
        null_handler: logging.NullHandler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self) -> None:
        """
        ## Add console output of log.
        """
        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self) -> None:
        """
        ## Add file output of log.
        """
        today_date: str = datetime.now().strftime("%Y%m%d")
        filename: str = f"{today_date}.log"

        log_path: Path = SETTINGS["log.dir"]
        if not log_path.exists():
            log_path.mkdir()
        file_path: Path = log_path.joinpath(filename)

        file_handler: logging.FileHandler = logging.FileHandler(
            file_path, mode="a", encoding="utf8"
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def register_event(self) -> None:
        """
        ## Register log event.
        """
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def process_log_event(self, event: Event) -> None:
        """
        ## Process log event.
        """
        log: LogData = event.data
        self.logger.log(log.level, log.msg)