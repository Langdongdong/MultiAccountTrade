from abc import ABC

from datetime import datetime
from typing import Any, Dict, Iterable, List

from base.setting import SETTINGS

from motor.core import (
    AgnosticClient, 
    AgnosticCollection,
    AgnosticCursor,
    AgnosticDatabase, 
)
from motor.motor_asyncio import AsyncIOMotorClient

from pymongo import (
    ASCENDING,
    ReplaceOne,
)

from pytz import timezone
from tzlocal import get_localzone_name

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

class MongoDatabase(ABC):
    def __init__(self) -> None:
        super().__init__()

        self.database: str = SETTINGS.get("database.database")
        self.host: str = SETTINGS.get("database.host",)
        self.port: str = SETTINGS.get("database.port")
        self.username: str = SETTINGS.get("database.username")
        self.password: str = SETTINGS.get("database.password")

        if self.username and self.password:
            self.client: AgnosticClient = AsyncIOMotorClient(
                host = self.host,
                port = self.port,
                username = self.username,
                password = self.password,
                tz_aware = True,
                tzinfo = timezone(get_localzone_name())
            )
        else:
            self.client: AgnosticClient = AsyncIOMotorClient(
                host = self.host,
                port = self.port,
                tz_aware = True,
                tzinfo = timezone(get_localzone_name())
            )

        self.db: AgnosticDatabase = self.client[self.database]

        self.bar_collection: AgnosticCollection = self.db["bar_data"]
        self.bar_collection.create_index(
            [
                ("symbol", ASCENDING),
                ("datetime", ASCENDING),
            ],
            unique=True
        )

    async def save_bar_data(self, bars: List[BarData]) -> bool:
        requests: List[ReplaceOne] = []
        
        # make it a async iterator????
        bars = aiter(bars)

        async for bar in bars:
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

        await self.bar_collection.bulk_write(requests, ordered=False)

        return True

    async def load_bar_data(
        self,
        symbol: str,
        start: str,
        end: str
    ) -> List[BarData]:
        """
        # Load bar data.
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

        c: AgnosticCursor = self.bar_collection.find(filter)
        
        bars: List[BarData] = []
        async for d in c:
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

    async def delete_bar_data(
        self,
        symbol: str,
        start: str,
        end: str
    ) -> int:
        start: datetime = datetime.strptime(start, "%Y%m%d")
        end:datetime = datetime.strptime(end, "%Y%m%d")

        filter: Dict[str, Any] = {
            "symbol": symbol,
            "datetime": {
                "$gte": start.astimezone(timezone(get_localzone_name())),
                "$lte": end.astimezone(timezone(get_localzone_name()))
            }
        }

        result = await self.bar_collection.delete_many(filter)
        return result.deleted_count

class aiter(Iterable):
    def __init__(self, iterable: Iterable) -> None:
        super().__init__()
        self.iterable = iterable
        self.count = 0

    async def next(self):
        if self.count == len[self.iterable]:
            self.count = 0
            return None
        val = self.iterable[self.count]
        self.count += 1
        return val

    def __aiter__(self):
        return self
 
    async def __anext__(self):
        val = await self.next()
        if val == None:
            raise StopAsyncIteration
        return val