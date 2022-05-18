import asyncio, pathlib, pandas, sys, re

from datetime import datetime
from typing import Set, Tuple

from config import ACCOUNT_SETTING, AM_SYMBOL_SETTING, FILE_SETTING
from utility import is_trade_period
from object import OrderAsking
from engine import MainEngine
from twap import TWAP
from utility import is_night_period

from vnpy.trader.constant import Direction



async def run():
    engine = MainEngine()

    # while True:
    #     if is_trade_period():
    #         current_time = datetime.now().time()
    #         if datetime.time(9,5) <= current_time or datetime.time(21,5) <= current_time:
    #             engine.log("Start trading")
    #             break
    #     await asyncio.sleep(5)

    # engine.connect()

    subscribes, queue = load_data(engine)

    # while True:
    #     not_inited_gateway_names = [gateway_name for gateway_name in engine.get_all_gateway_names() if not engine.is_gateway_inited(gateway_name)]
    #     if not not_inited_gateway_names:
    #         break
    #     await asyncio.sleep(3)

    # engine.susbcribe(subscribes)
    # await asyncio.sleep(3)

    # tasks = []
    # for i in range(len(engine.gateways) * 10):
    #     tasks.append(asyncio.create_task(run_twap(engine, queue)))

    # await queue.join()
    # engine.log("Complete all TWAP")

    # await asyncio.gather(*tasks, return_exceptions=True)

    # save_position(engine)
    # engine.log("Positions files saved")

    engine.close()
    sys.exit()


async def run_twap(engine: MainEngine, queue: asyncio.Queue):
    while not queue.empty():
        data = await queue.get()
        twap = TWAP(engine, data[0], data[1])
        await twap.run()
        queue.task_done()

def load_data(engine: MainEngine) -> Tuple[Set[str], asyncio.Queue]:
    """
    Load and process data from the specified csv file.\n
    Output a set of symbol subscriptions and a queue of order requests.
    """   
    subscribes: Set[str] = set()
    queue: asyncio.Queue = asyncio.Queue()

    try:
        iter = pathlib.Path(engine.get_load_dir_path()).iterdir()
        last = next(iter)
        for last in iter: pass
        file_date = re.match("[0-9]*",last.name).group()
    except:
        engine.log("SFTP remote server has not be turned on.")
        sys.exit(0)

    for gateway_name in engine.get_all_gateway_names():
        engine.add_load_file_path(gateway_name, f"{file_date}_{gateway_name}.csv")
        engine.add_backup_file_path(gateway_name, f"{file_date}_{gateway_name}_backup.csv")

        requests: pandas.DataFrame = engine.load_data(gateway_name)

        subscribes.update([OrderAsking.convert_to_vt_symbol(symbol) for symbol in requests["ContractID"].tolist()])
        if engine.is_night_trading_time():
            subscribes = engine.filter_am_symbol(subscribes)
            # requests = requests[requests["ContractID"].apply(lambda x:(re.match("[^0-9]*", x, re.I).group().upper() not in AM_SYMBOL_SETTING))]
        
        for row in requests.itertuples():
            request = OrderAsking(getattr(row, "ContractID"), getattr(row, "Op1"), getattr(row, "Op2"), getattr(row, "Num"))
            if request.vt_symbol in subscribes:
                queue.put_nowait((gateway_name, request))

    return subscribes, queue


def save_position(engine: MainEngine) -> None:
    position_dir_path = pathlib.Path(FILE_SETTING.get("POSITION_DIR_PATH"))

    for gateway_name in engine.get_all_gateway_names():
        gateway_position: pandas.DataFrame = engine.get_gateway_positions(gateway_name, True)
        gateway_position = gateway_position[gateway_position["volume"] is not 0]
        gateway_position = gateway_position[["symbol", "direction", "volume"]]
        gateway_position["direction"] = gateway_position["direction"].apply(lambda x : "Buy" if x == Direction.LONG else "Sell")
        gateway_position.sort_values(["direction", "symbol"], ascending = [True, True], inplace = True)

        position_file_path = position_dir_path.joinpath(f"{datetime.now().strftime('%Y%m%d')}_{gateway_name}_positions.csv")
        gateway_position.to_csv(position_file_path, index = False)
        

if __name__ == "__main__":
    asyncio.run(run())