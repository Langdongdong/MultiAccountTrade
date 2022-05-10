import asyncio, pathlib, pandas, sys, re
from typing import Dict, Set, Tuple

from pandas import DataFrame
from constant import OrderRequest
from engine import BackupEngine, MAEngine

from vnpy_ctp import CtpGateway
from vnpy_rohon import RohonGateway

from twap import TWAP
from utility import is_night_period

AM_SYMBOL = []

TWAP_SETTING = {
    "TIME": 60,
    "INTERVAL": 30
}

FILE_SETTING = {
    "ORDER_DIR_PATH": "",
    "BACKUP_DIR_PATH": "",
    "POSITION_DIR_PATH": "",
}

ACCOUNT_SETTING = {
    "account_name_01": {
        "用户名": "",
        "密码": "",
        "经纪商代码": "",
        "交易服务器": "",
        "行情服务器": "",
        "产品名称": "",
        "授权编码": "",
        "Gateway": "CtpGateway"
    },
    "account_name_02": {
        "用户名": "",
        "密码": "",
        "经纪商代码": "",
        "交易服务器": "",
        "行情服务器": "",
        "产品名称": "",
        "授权编码": "",
        "Gateway": "RohonGateway"
    }
}

async def run():
    engine = MAEngine([CtpGateway, RohonGateway], ACCOUNT_SETTING)
    subscribes, queue = load_data(engine)
    while True: 
        if engine.is_gateway_inited(engine.get_subscribe_gateway().gateway_name):
            engine.susbcribe(subscribes)
            break
        asyncio.sleep(3)

    tasks = []
    for i in range(len(engine.gateways) * 5):
        tasks.append(asyncio.create_task(run_twap(engine, queue)))

    await queue.join()

    await asyncio.gather(*tasks, return_exceptions=True)

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

    for gateway in engine.get_all_gateways():
        order_file_path = order_dir_path.joinpath(f"{file_date}_{gateway.gateway_name}.csv")
        backup_file_path = backup_dir_path.joinpath(f"{file_date}_{gateway.gateway_name}_backup.csv")
        
        backup_engine: BackupEngine = engine.get_engine("backup")
        backup_engine.add_backup_file_path(gateway.gateway_name, backup_file_path)

        requests: DataFrame = backup_engine.load_backup_file_path(gateway.gateway_name)
        if requests is None:
            requests = pandas.read_csv(order_file_path)
            backup_engine.add_backup_data(gateway.gateway_name, requests)
            backup_engine.backup(gateway.gateway_name)

        if is_night_period():
            requests = requests[requests["ContractID"].apply(lambda x:(re.match("[^0-9]*", x, re.I).group().upper() not in AM_SYMBOL))]
        
        for row in requests.itertuples():
            if getattr(row, "Num") <= 0:
                continue
            request = OrderRequest(getattr(row, "ContractID"), getattr(row, "Op1"), getattr(row, "Op2"), getattr(row, "Num"))
            queue.put_nowait((gateway.gateway_name, request))

        subscribes.update([OrderRequest.convert_to_vt_symbol(symbol) for symbol in requests["ContractID"].tolist()])

    return subscribes, queue

if __name__ == "__main__":
    pass