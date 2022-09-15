from strategy.template import StrategyTemplate

from base.engine import CtpEngine

class TestStrategy(StrategyTemplate):
    def __init__(self, ctp_engine: CtpEngine) -> None:
        super().__init__(ctp_engine)