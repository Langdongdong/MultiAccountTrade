from cgitb import handler
from collections import defaultdict
from datetime import datetime
from enum import Enum
from queue import Empty, Queue
from threading import Thread
from typing import Any, Callable,  Dict, List

from pymongo import ASCENDING, MongoClient, ReplaceOne
from pymongo.cursor import Cursor
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult

from pytz import timezone
from tzlocal import get_localzone_name

from base.setting import SETTINGS

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import TickData, BarData


class DatabaseEventType(Enum):
    SAVE_BAR = 0,
    LOAD_BAR = 1,
    DELETE_BAR = 2

class DatabaseEvent:
    def __init__(self, type: DatabaseEventType, data: Any = None) -> None:
        """"""
        self.type: str = type
        self.data: Any = data

class MongoDatabase():
    """
    # Mongodb to save data.
    """
    def __init__(self) -> None:
        super().__init__()

        self.active: bool = False

        self.queue: Queue = Queue()
        self.thread: Thread = Thread(target=self.run)
        self.handlers: defaultdict = defaultdict(set)

        self.database: str = SETTINGS.get("database.database")
        self.host: str = SETTINGS.get("database.host",)
        self.port: str = SETTINGS.get("database.port")
        self.username: str = SETTINGS.get("database.username")
        self.password: str = SETTINGS.get("database.password")

        if self.username and self.password:
            self.client: MongoClient = MongoClient(
                host = self.host,
                port = self.port,
                username = self.username,
                password = self.password,
                tz_aware = True,
                tzinfo = timezone(get_localzone_name())
            )
        else:
            self.client: MongoClient = MongoClient(
                host = self.host,
                port = self.port,
                tz_aware = True,
                tzinfo = timezone(get_localzone_name())
            )

        self.db: Database = self.client[self.database]

        self.bar_collection: Collection = self.db["bar_data"]
        self.bar_collection.create_index(
            [
                ("symbol", ASCENDING),
                ("datetime", ASCENDING),
            ],
            unique=True
        )

        self.tick_collection: Collection = self.db["tick_data"]
        self.tick_collection.create_index(
            [
                ("symbol", ASCENDING),
                ("datetime", ASCENDING),
            ],
            unique=True
        )

    def run(self) -> None:
        while self.active:
            try:
                event: DatabaseEvent = self.queue.get(block=True, timeout=1)
                self.process(event)
            except Empty:
                pass

    def process(self, event: DatabaseEvent) -> None:
        if event.type in self.handlers:
            [handler[event] for handler in self.handlers[event.type]]

    def register(self, type: DatabaseEventType, handler: Callable[[DatabaseEvent], None]):
        handler_list: list = self.handlers[type]
        if handler not in handler_list:
            handler_list.append(handler)

    def put(self, event: DatabaseEvent) -> None:
        self.queue.put(event)

    def start(self) -> None:
        self.active = True
        self.thread.start()

    def stop(self) -> None:
        self.active = False
        self.thread.join()


        

    def process_save_bar_event(self,event: DatabaseEvent) -> bool:
        """
        # Process save bar data event.
        """
        bars: List[BarData] = event.data

        requests: List[ReplaceOne] = []

        for bar in bars:
            filter: Dict[str, Any] = {
                "symbol": bar.symbol,
                "datetime": bar.datetime
            }

            d: Dict[str, Any] = {
                "symbol": bar.symbol,
                "exchange": bar.exchange.value,
                "interval": bar.interval.value,
                "open": bar.open_price,
                "close": bar.close_price,
                "high": bar.high_price,
                "low": bar.low_price,
                "volume": bar.volume,
                "money": bar.turnover,
                "avg": bar.avg_price,
                "high_limit": bar.limit_up,
                "low_limit": bar.limit_down,
                "pre_close": bar.pre_close,
                "open_interest": bar.open_interest,
                "datetime": bar.datetime,
            }

            requests.append(ReplaceOne(filter, d, upsert=True))

        self.bar_collection.bulk_write(requests, ordered=False)
        return True

    def load_bar_data(self, event: DatabaseEvent) -> List[BarData]:
        """
        # Process load bar data event.
        """


        start: datetime = datetime.strptime(start, "%Y%m%d")
        end:datetime = datetime.strptime(end, "%Y%m%d")

        filter: Dict[str, Any] = {
            "symbol": symbol,
            "datetime": {
                "$gte": start.astimezone(timezone(get_localzone_name())),
                "$lte": end.astimezone(timezone(get_localzone_name()))
            }
        }

        c: Cursor = self.bar_collection.find(filter)

        bars: List[BarData] = []
        for d in c:
            d["exchange"] = Exchange(d["exchange"])
            d["interval"] = Interval(d["interval"])
            d["gateway_name"] = "DB"
            d.pop("_id")

            bar = BarData(
                symbol=d["symbol"],
                exchange=d["exchange"],
                interval=d["interval"],
                gateway_name=d["gateway_name"],
                open_price=d["open"],
                close_price=d["close"],
                high_price=d["high"],
                low_price=d["low"],
                volume=d["volume"],
                turnover=d["money"],
                avg_price=d["avg"],
                limit_up=d["high_limit"],
                limit_down=d["low_limit"],
                pre_close=d["pre_close"],
                open_interest=d["open_interest"],
                datetime=d["datetime"]
            )
            bars.append(bar)
        
        return bars

    def delete_bar_data(
        self,
        symbol: str
    ) -> int:
        """
        # Delete bar data.
        """
        filter: Dict[str, Any] = {
            "symbol": symbol
        }

        result: DeleteResult = self.bar_collection.delete_many(filter)

        return result.deleted_count