from typing import Any, Dict, List
from pymongo import MongoClient
from base.object import BarData
from base.setting import settings

class MongoDatabase:
    def __init__(self) -> None:
        self.host: str = settings.get("database.host",)
        self.port: str = settings.get("database.port")
        self.username: str = settings.get("database.username")
        self.password: str = settings.get("database.password")

        if self.username and self.password:
            self.client: MongoClient = MongoClient(
                host = self.host,
                port = self.port,
                username = self.username,
                password = self.password
            )
        else:
            self.client: MongoClient = MongoClient(
                host = self.host,
                port = self.port
            )

    def insert_bar_data(self, bars: List[BarData]) -> None:
        for bar in bars:
            filter: Dict[str, Any] = {
                "date": bar.date
            }
