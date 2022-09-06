from datetime import datetime, timedelta
from typing import Any, Dict, List

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

class MongoDatabase():
    """
    # Mongodb to save data.
    ## Note:
    ## 1. Auto attach store date to the collection name.
    """
    def __init__(self) -> None:
        super().__init__()

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

    def save_bar_data(
        self,
        bars: List[BarData]
    ) -> bool:
        """
        # Save bar data.
        """
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

    def load_bar_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime
    ) -> List[BarData]:
        """
        # Load bar data.
        """
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

    def save_tick_data(
        self,
        ticks: List[TickData]
    )-> bool:
        """
        # Save tick data.
        """
        requests: List[ReplaceOne] = []

        for tick in ticks:
            filter: dict = {
                "symbol": tick.symbol,
                "datetime": tick.datetime,
            }

            d: dict = {
                "symbol": tick.symbol,
                "exchange": tick.exchange.value,
                "datetime": tick.datetime,
                "name": tick.name,
                "volume": tick.volume,
                "turnover": tick.turnover,
                "open_interest": tick.open_interest,
                "last_price": tick.last_price,
                "last_volume": tick.last_volume,
                "limit_up": tick.limit_up,
                "limit_down": tick.limit_down,
                "open_price": tick.open_price,
                "high_price": tick.high_price,
                "low_price": tick.low_price,
                "pre_close": tick.pre_close,
                "bid_price_1": tick.bid_price_1,
                "bid_price_2": tick.bid_price_2,
                "bid_price_3": tick.bid_price_3,
                "bid_price_4": tick.bid_price_4,
                "bid_price_5": tick.bid_price_5,
                "ask_price_1": tick.ask_price_1,
                "ask_price_2": tick.ask_price_2,
                "ask_price_3": tick.ask_price_3,
                "ask_price_4": tick.ask_price_4,
                "ask_price_5": tick.ask_price_5,
                "bid_volume_1": tick.bid_volume_1,
                "bid_volume_2": tick.bid_volume_2,
                "bid_volume_3": tick.bid_volume_3,
                "bid_volume_4": tick.bid_volume_4,
                "bid_volume_5": tick.bid_volume_5,
                "ask_volume_1": tick.ask_volume_1,
                "ask_volume_2": tick.ask_volume_2,
                "ask_volume_3": tick.ask_volume_3,
                "ask_volume_4": tick.ask_volume_4,
                "ask_volume_5": tick.ask_volume_5,
                "localtime": tick.localtime,
            }

            requests.append(ReplaceOne(filter, d, upsert=True))

        self.tick_collection.bulk_write(requests, ordered=False)
        return True

    def load_tick_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime
    ) -> List[TickData]:
        """
        # Load tick data.
        """
        filter: dict = {
            "symbol": symbol,
            "datetime": {
                "$gte": start.astimezone(timezone(get_localzone_name())),
                "$lte": end.astimezone(timezone(get_localzone_name()))
            }
        }
        c: Cursor = self.tick_collection.find(filter)

        ticks: List[TickData] = []
        for d in c:
            d["exchange"] = Exchange(d["exchange"])
            d["gateway_name"] = "DB"
            d.pop("_id")

            tick: TickData = TickData(**d)
            ticks.append(tick)

        return ticks

    def delete_tick_data(
        self,
        symbol: str,
    ) -> int:
        """
        # Delete tick data.
        """
        filter: dict = {
            "symbol": symbol
        }

        result: DeleteResult = self.tick_collection.delete_many(filter)

        return result.deleted_count

    # def get_store_date(self) -> str:
    #     store_time = datetime.now()

    #     if CtpEngine.is_night_trading_time():
    #         store_time = store_time + timedelta(days=1)

    #         if store_time.weekday() == 5:
    #             store_time = store_time + timedelta(days=2)

    #     return store_time.strftime("%Y%m%d")
