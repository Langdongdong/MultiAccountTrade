from engine import MainEngine, BarEngine
from vnpy.trader.object import BarData

def on_bar(bar: BarData):
    print(bar)

if __name__ == "__main__":
    engine = MainEngine()
    bar_engine: BarEngine = engine.add_engine(BarEngine)
    bar_engine.init(5, on_bar)

    engine.connect()

    engine.susbcribe({"rb2210.SHFE"})