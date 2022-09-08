import sys
from time import sleep
sys.path.append('.')

from threading import Thread

from base.engine import CtpEngine
from base.joinquant import get_dominant_symbols
from base.setting import ACCOUNTS

ACTIVE = False

def run(ctp_engine: CtpEngine):

    ctp_engine.connect_all(ACCOUNTS)

    ctp_engine.subscribe(get_dominant_symbols(ctp_engine))


if __name__ == "__main__":
    ctp_engine = CtpEngine()

    ctp_engine_thread = Thread(target=run,args=(ctp_engine,))

    while True:
        if not ACTIVE and CtpEngine.is_trading_time():
            ACTIVE = True

            ctp_engine_thread.start()

        if ACTIVE and not CtpEngine.is_trading_time():
            ACTIVE = False

            ctp_engine.close()

            ctp_engine_thread.join()

            break

        sleep(60)

        ctp_engine.write_log(len([bg for bg in ctp_engine.get_all_bar_generators() if bg.bar]))