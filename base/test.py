from time import sleep
from engine import MainEngine
from utility import BarGenerator
from vnpy.trader.object import BarData

def on_bar(bar: BarData):
    print(bar)

if __name__ == "__main__":
    engine = MainEngine()

    engine.connect()

    engine.susbcribe({"rb2210.SHFE"})

    bg = BarGenerator(engine.event_engine, 5, on_bar)


    
    # engine.close()