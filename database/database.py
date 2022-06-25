from abc import ABC, abstractmethod
from typing import Any, List


class BaseDatabase(ABC):
    @abstractmethod
    def insert_bar_data(self, bars: List[Any]) -> bool:
        pass

    @abstractmethod
    def load_bar_data(self, symbol: str) -> List[Any]:
        pass

    @abstractmethod
    def delete_bar_data(self, symbol: str) -> int:
        pass