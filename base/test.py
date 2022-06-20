from time import sleep
from engine import MainEngine, BarEngine

if __name__ == "__main__":
    engine = MainEngine()
    bar_engine = engine._add_engine(BarEngine)

    engine.connect()
    engine.susbcribe({"rb2210.SHFE"})
    data = engine.get_all_contracts(True)
    while True:
        print(engine.get_tick("rb2210.SHFE"))
        sleep(1)

    
    # engine.close()