
from abc import ABC, abstractmethod

from cta_engine import CtaEngine


class CtaTemplate(ABC):
    def __init__(self, cta_engine: CtaEngine) -> None:
        self.cta_engine = cta_engine

    
    
    @abstractmethod
    def on_init(self) -> None:
        pass

    @abstractmethod
    def on_start(self) -> None:
        pass

    @abstractmethod
    def on_stop(self) -> None:
        pass

    @abstractmethod
    def on_tick(self) -> None:
        pass

    @abstractmethod
    def on_bar(self) -> None:
        pass

    @abstractmethod
    def on_order(self) -> None:
        pass

    @abstractmethod
    def on_trade(self) -> None:
        pass

    
