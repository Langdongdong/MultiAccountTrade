from typing import Any, Dict, List

from pymongo import MongoClient, ReplaceOne
from pymongo.cursor import Cursor
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult

from pytz import timezone
from tzlocal import get_localzone_name

from .database import BaseDatabase
from base.object import BarData
from base.setting import settings

class MongoDatabase(BaseDatabase):
    def __init__(self, collection_name: str = "") -> None:
        super().__init__()

        self.name: str = settings.get("database.name")
        self.host: str = settings.get("database.host",)
        self.port: str = settings.get("database.port")
        self.username: str = settings.get("database.username")
        self.password: str = settings.get("database.password")

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

        self.database: Database = self.client.get_database(self.name)

        if collection_name:
            self.collection: Collection = self.database.get_collection(collection_name)

    def set_collection(self, collection_name: str) -> None:
        self.collection = self.database.get_collection(collection_name)

    def insert_bar_data(self, bars: List[BarData]) -> bool:
        requests: List[ReplaceOne] = []

        for bar in bars:
            filter: Dict[str, Any] = {
                "symbol": bar.symbol,
                "date": bar.date
            }

            data: Dict[str, Any] = {
                "symbol": bar.symbol,
                "open": bar.open,
                "close": bar.close,
                "high": bar.high,
                "low": bar.low,
                "volume": bar.volume,
                "money": bar.money,
                "avg": bar.avg,
                "high_limit": bar.high_limit,
                "low_limit": bar.low_limit,
                "pre_close": bar.pre_close,
                "open_interest": bar.open_interest,
                "date": bar.date
            }

            requests.append(ReplaceOne(filter, data, True))

        self.collection.bulk_write(requests, ordered=False)

        return True

    def load_bar_data(self, symbol: str) -> List[BarData]:
        filter: Dict[str, Any] = {
            "symbol": symbol
        }

        cursor: Cursor = self.collection.find(filter)

        bars: List[BarData] = []
        for data in cursor:
            data.pop("_id")

            bar = BarData(**data)
            bars.append(bar)
        
        return bars

    def delete_bar_data(self, symbol: str) -> int:
        filter: Dict[str, Any] = {
            "symbol": symbol
        }

        result: DeleteResult = self.collection.delete_many(filter)

        return result.deleted_count