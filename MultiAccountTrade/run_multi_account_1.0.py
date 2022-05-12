import asyncio, pathlib, pandas, sys, re

from datetime import datetime
from typing import Dict, Set, Tuple

from MultiAccountTrade.config import ACCOUNT_SETTING, AM_SYMBOL, FILE_SETTING, TWAP_SETTING
from MultiAccountTrade.utility import is_trade_period
from object import OrderRequest
from engine import MAEngine
from twap import TWAP
from utility import is_night_period

from vnpy.trader.constant import Direction
from vnpy_ctp import CtpGateway
from vnpy_rohon import RohonGateway


async def run():
    print(">>>>> START SCRIPT >>>>>")
    while True:
        if is_trade_period():
            print(">>>>> START TRADING >>>>>")
            break
        await asyncio.sleep(5)

    engine = MAEngine([CtpGateway, RohonGateway], ACCOUNT_SETTING)
    engine.debug("Engine inited")

    subscribes, queue = load_data(engine)
    engine.debug("Data loaded")

    while True: 
        if engine.is_gateway_inited(engine.get_subscribe_gateway().gateway_name):
            engine.susbcribe(subscribes)
            break
        asyncio.sleep(3)
    engine.debug("Symbols subscribed")

    while True:
        not_inited_gateway_names = [n for n in engine.get_all_gateway_names() if not engine.is_gateway_inited(n)]
        if len(not_inited_gateway_names) == 0:
            break
        await asyncio.sleep(3)
    engine.debug("All gateways inited")
    
    tasks = []
    for i in range(len(engine.gateways) * 5):
        tasks.append(asyncio.create_task(run_twap(engine, queue, TWAP_SETTING)))

    await queue.join()
    engine.debug("Complete all TWAP")

    await asyncio.gather(*tasks, return_exceptions=True)

    save_position(engine)
    engine.debug("Positions saved")

    engine.close()
    sys.exit()

async def run_twap(engine: MAEngine, queue: asyncio.Queue, twap_setting: Dict[str, int]):
    while not queue.empty():
        data = await queue.get()

        await TWAP(engine, data[0], data[1], twap_setting).run()

        queue.task_done()

def load_data(engine: MAEngine) -> Tuple[Set[str], asyncio.Queue]:
    """
    Load and process data from the specified csv file.\n
    Output a set of symbol subscriptions and a queue of order requests.
    """   
    subscribes: Set[str] = set()
    queue: asyncio.Queue = asyncio.Queue()

    order_dir_path = pathlib.Path(FILE_SETTING["ORDER_DIR_PATH"])
    backup_dir_path = pathlib.Path(FILE_SETTING["BACKUP_DIR_PATH"])
    if not backup_dir_path.exists():
        backup_dir_path.mkdir()

    try:
        iter = order_dir_path.iterdir()
        last = next(iter)
        for last in iter: pass
        file_date = re.match("[0-9]*",last.name).group()
    except:
        print("SFTP remote server has not be turned on.")
        sys.exit(0)

    for gateway_name in engine.get_all_gateway_names():
        order_file_path = order_dir_path.joinpath(f"{file_date}_{gateway_name}.csv")
        backup_file_path = backup_dir_path.joinpath(f"{file_date}_{gateway_name}_backup.csv")
        engine.add_backup_file_path(gateway_name, backup_file_path)

        requests: pandas.DataFrame = engine.load_backup_data(gateway_name)
        if requests is None:
            requests = pandas.read_csv(order_file_path)
            engine.add_backup_data(gateway_name, requests)
            engine.backup(gateway_name)

        if is_night_period():
            requests = requests[requests["ContractID"].apply(lambda x:(re.match("[^0-9]*", x, re.I).group().upper() not in AM_SYMBOL))]
        
        for row in requests.itertuples():
            if getattr(row, "Num") <= 0:
                continue
            request = OrderRequest(getattr(row, "ContractID"), getattr(row, "Op1"), getattr(row, "Op2"), getattr(row, "Num"))
            queue.put_nowait((gateway_name, request))

        subscribes.update([OrderRequest.convert_to_vt_symbol(symbol) for symbol in requests["ContractID"].tolist()])

    return subscribes, queue

def save_position(engine: MAEngine) -> None:
    positions: pandas.DataFrame = engine.get_all_positions(True)
    position_dir_path = pathlib.Path(FILE_SETTING["POSITION_DIR_PATH"])

    positions["direction"] = positions["direction"].apply(lambda x : "Buy" if x == Direction.LONG else "Sell")
    positions.sort_values(["direction", "symbol"], ascending = [True, True], inplace = True)
    positions = positions[positions["volume"] != 0]

    for gateway_name in engine.get_all_gateway_names():
        positon_file_path = position_dir_path.joinpath(f"{datetime.now().strftime('%Y%m%d')}_{gateway_name}_positions.csv")

        position : pandas.DataFrame = positions[position["gatewway_name"] == gateway_name]
        position = position[["symbol","direction","volume"]]
        position.to_csv(positon_file_path, index = False)


if __name__ == "__main__":
    asyncio.run(run())