import asyncio, pathlib, pandas, sys, re
from time import sleep

from datetime import datetime
from typing import Set, Tuple

from config import FILE_SETTING
from engine import MainEngine, DataEngine
from object import OrderAsking
from sniper_algo import SniperAlgo

from vnpy.trader.constant import Direction



async def run():
    engine = MainEngine()

    while True:
        if engine.is_trading_time():
            break
        sleep(10)

    subscribes, queue = load_data(engine)

    engine.connect()

    engine.susbcribe(subscribes)

    tasks = []
    for i in range(len(engine.gateways) * 10):
        tasks.append(asyncio.create_task(run_algo(engine, queue)))

    await queue.join()
    await asyncio.gather(*tasks, return_exceptions=True)

    save_position(engine)
    engine.log("Position saved")
    
    engine.close()
    
    print("Exit")
    sys.exit()

async def run_algo(engine: MainEngine, queue: asyncio.Queue):
    while not queue.empty():
        data = await queue.get()
        await SniperAlgo(engine, data[0], data[1]).run()
        queue.task_done()

def load_data(engine: MainEngine) -> Tuple[Set[str], asyncio.Queue]:
    """
    Load and process data from the specified csv file.
    
    Output a set of symbol subscriptions and a queue of order requests.
    """   
    subscribes: Set[str] = set()
    queue: asyncio.Queue = asyncio.Queue()
    data_engine: DataEngine = engine.get_engine(DataEngine.__name__)
    if data_engine is None:
        return

    try:
        iter = pathlib.Path(data_engine.get_load_dir_path()).iterdir()
        last = next(iter)
        for last in iter: pass
        file_date = re.match("[0-9]*",last.name).group()
    except:
        engine.log("SFTP remote server has not be turned on.")
        engine.close()
        sys.exit()

    for gateway_name in engine.get_all_gateway_names():
        requests: pandas.DataFrame = data_engine.load_data(gateway_name, f"{file_date}_{gateway_name}.csv")
        requests = requests[requests["Num"] > 0]

        subscribes.update([OrderAsking.convert_to_vt_symbol(symbol) for symbol in requests["ContractID"].tolist()])
        if engine.is_night_trading_time():
            subscribes = engine.filter_am_symbol(subscribes)
        
        for row in requests.itertuples():
            request = OrderAsking(getattr(row, "ContractID"), getattr(row, "Op1"), getattr(row, "Op2"), getattr(row, "Num"))
            if request.vt_symbol in subscribes:
                queue.put_nowait((gateway_name, request))

    return subscribes, queue


def save_position(engine: MainEngine) -> None:
    position_dir_path = pathlib.Path(FILE_SETTING.get("POSITION_DIR_PATH"))

    for gateway_name in engine.get_all_gateway_names():
        gateway_position: pandas.DataFrame = engine.get_gateway_positions(gateway_name, True)
        gateway_position = gateway_position[gateway_position["volume"] != 0]
        gateway_position = gateway_position[["symbol", "direction", "volume"]]
        gateway_position["direction"] = gateway_position["direction"].apply(lambda x : "Buy" if x == Direction.LONG else "Sell")
        gateway_position.sort_values(["direction", "symbol"], ascending = [True, True], inplace = True)

        position_file_path = position_dir_path.joinpath(f"{datetime.now().strftime('%Y%m%d')}_{gateway_name}_positions.csv")
        gateway_position.to_csv(position_file_path, index = False)
        

if __name__ == "__main__":
    asyncio.run(run())