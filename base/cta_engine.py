
from engine import BaseEngine, MainEngine
from vnpy.event import EventEngine


class CtaEngine(BaseEngine):
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, engine_name: str) -> None:
        super().__init__(main_engine, event_engine, engine_name)
