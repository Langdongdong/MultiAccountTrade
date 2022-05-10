import asyncio, pathlib, pandas, math, sys, re

from constant import *
from utility import *

from vnpy.trader.constant import Direction, Offset
from vnpy_scripttrader import init_cli_trading, ScriptEngine
from vnpy_ctp import CtpGateway


async def run_async():

    print(f"{datetime.datetime.now()} Start script.")
    while True:
        if is_trade_period():
            print(f"{datetime.datetime.now()} Time to trade.")
            break
        await asyncio.sleep(5)

    print(f"{datetime.datetime.now()} Load data.")
    df_order = load_df_order()
    vt_subs = list(set([convert_to_vt_symbol(i) for i in df_order.ContractID.tolist()]))
    
    queue = asyncio.Queue()
    for row in df_order.itertuples():
        if getattr(row, "Num") <= 0:
            continue
        queue.put_nowait(row)
    

    print(f"{datetime.datetime.now()} Start Engine.")
    engine: ScriptEngine = init_cli_trading([CtpGateway])
    engine.connect_gateway(CTP_SETTING, "CTP")
    await asyncio.sleep(10)
    
    while True:
        if engine.main_engine.get_gateway("CTP").td_api.contract_inited:
            break
        await asyncio.sleep(3)

    while True:
        tmp_vt_subs = [s for s in vt_subs if not engine.get_tick(s)]
        if len(tmp_vt_subs) == 0:
            break
        engine.subscribe(tmp_vt_subs)
        await asyncio.sleep(3)

    print(f"{datetime.datetime.now()} Start TWAP algo.")
    tasks = []
    for i in range(queue.qsize()):
        tasks.append(asyncio.create_task(run_twap_algo(engine, queue)))
        
    await queue.join()
    await asyncio.gather(*tasks, return_exceptions=True)
    print(f"{datetime.datetime.now()} All order request done.")

    if datetime.time(9,5) <= datetime.datetime.now().time() <= datetime.time(14,50):
        await save_df_pos(engine)
        print(f"{datetime.datetime.now()} Save pos csv.")

    engine.main_engine.close()
    print(f"{datetime.datetime.now()} Exit script.")
    sys.exit(0)


async def run_twap_algo(engine: ScriptEngine, queue: asyncio.Queue):
    while not queue.empty():
        req = await queue.get()

        vt_symbol = convert_to_vt_symbol(getattr(req, "ContractID"))
        order_type = convert_to_vt_order_type(getattr(req, "Op1"), getattr(req, "Op2"))
        total_vol = float(getattr(req, "Num"))

        traded_vol = 0.0
        order_vol = get_twap_vol(total_vol)

        while traded_vol < total_vol:
            order_vol = min(order_vol, total_vol - traded_vol)

            vt_orderids = await send_order(engine, vt_symbol, order_vol, order_type)
            print(f"{datetime.datetime.now()} {vt_symbol} send order {order_type.value} {order_vol}.")

            await asyncio.sleep(TWAP_SETTING['INTERVAL'])

            traded_vol = await update_traded_vol(engine, vt_orderids, traded_vol)
            print(f"{datetime.datetime.now()} {vt_symbol} has traded {traded_vol} left {total_vol - traded_vol}.")

            backup_df_order(req, total_vol - traded_vol)

        print(f"{datetime.datetime.now()} {vt_symbol} {order_type.value} {total_vol} order request done.")
        queue.task_done()


async def send_order(engine: ScriptEngine, vt_symbol: str, volume: float, order_type: OrderMode, is_taker: bool = True):
    # Make sure to get tick data.
    while True:
        tick = engine.get_tick(vt_symbol)
        pricetick = engine.get_contract(vt_symbol).pricetick
        if tick and pricetick:
            break
        await asyncio.sleep(0.5)
    
    vt_orderids = []

    if order_type == OrderMode.BUY:
        if not is_taker: price = tick.bid_price_1
        else: price = tick.ask_price_1 + pricetick * 2
        vt_orderids.append(engine.buy(vt_symbol, price, volume))

    elif order_type == OrderMode.SELL:
        if not is_taker: price = tick.ask_price_1
        else: price = tick.bid_price_1 - pricetick * 2

        if vt_symbol.split(".")[1] in [Exchange.SHFE.value, Exchange.INE.value]:
            while True:
                pos = engine.get_position(f"{vt_symbol}.{Direction.LONG.value}")
                if pos:
                    break
                await asyncio.sleep(0.5)
            yd_vol = pos.yd_volume
            if not yd_vol:
                vt_orderids.append(engine.send_order(vt_symbol, price, volume, Direction.SHORT, Offset.CLOSETODAY))
            elif yd_vol < volume:
                vt_orderids.append(engine.send_order(vt_symbol, price, yd_vol, Direction.SHORT, Offset.CLOSEYESTERDAY))
                vt_orderids.append(engine.send_order(vt_symbol, price, volume - yd_vol, Direction.SHORT, Offset.CLOSETODAY))
  
        vt_orderids.append(engine.sell(vt_symbol, price, volume))

    elif order_type == OrderMode.SHORT:
        if not is_taker: price = tick.ask_price_1
        else: price = tick.bid_price_1 - pricetick * 2
        vt_orderids.append(engine.short(vt_symbol, price, volume))

    elif order_type == OrderMode.COVER:
        if not is_taker: price = tick.bid_price_1
        else: price = tick.ask_price_1 + pricetick * 2

        if vt_symbol.split(".")[1] in [Exchange.SHFE.value, Exchange.INE.value]:
            while True:
                pos = engine.get_position(f"CTP.{vt_symbol}.{Direction.SHORT.value}")
                if pos:
                    break
                await asyncio.sleep(0.5)
            yd_vol = pos.yd_volume
            if not yd_vol:
                vt_orderids.append(engine.send_order(vt_symbol, price, volume, Direction.LONG, Offset.CLOSETODAY))
            elif yd_vol < volume:
                vt_orderids.append(engine.send_order(vt_symbol, price, yd_vol, Direction.LONG, Offset.CLOSEYESTERDAY))
                vt_orderids.append(engine.send_order(vt_symbol, price, volume - yd_vol, Direction.LONG, Offset.CLOSETODAY))
                return vt_orderids

        vt_orderids.append(engine.cover(vt_symbol, price, volume))

    return vt_orderids
    

async def update_traded_vol(engine: ScriptEngine, vt_orderids: list, traded_vol: float):
    for id in vt_orderids:
        while True:
            order = engine.get_order(id)
            if order:
                if order.is_active():
                    engine.cancel_order(id)
                break
            await asyncio.sleep(0.5)

    await asyncio.sleep(3)
    
    for id in vt_orderids:
        while True:
            order = engine.get_order(id)
            if order:
                if order.traded:
                    traded_vol += order.traded
                break
            await asyncio.sleep(0.5)
    
    return traded_vol


def load_df_order():
    try:
        iter = pathlib.Path(CSV_SETTING["CSV_ORDER_DIR_PATH"]).glob(f"*{CSV_SETTING['CSV_ACCOUNT']}*")
        last = next(iter)
        for last in iter: pass
        file_date = re.match("[0-9]*",last.name).group()
    except:
        print("SFTP remote server has not be turned on.")
        sys.exit(0)

    backup_csv_dir_path = pathlib.Path(CSV_SETTING["CSV_BACKUP_DIR_PATH"])
    if not backup_csv_dir_path.exists():
        backup_csv_dir_path.mkdir()

    backup_csv_path = backup_csv_dir_path.joinpath(f"BACKUP_{file_date}_{CSV_SETTING['CSV_ACCOUNT']}.csv")
    if backup_csv_path.exists():
        df_order = pandas.read_csv(backup_csv_path)
    else:
        df_order = pandas.read_csv(last)
        df_order.to_csv(backup_csv_path,index=False)
    
    if is_night_period():
        df_order = df_order[df_order["ContractID"].apply(lambda x:(re.match("[^0-9]*", x, re.I).group().upper() not in SYMBOL_AM))]
    
    return df_order


def get_twap_vol(volume: float) -> float:
        if volume == 1.0:
            return volume
        return max(float(math.floor(volume / (TWAP_SETTING['TIME'] / TWAP_SETTING['INTERVAL']))), 1.0)


def backup_df_order(req, left_vol:float):
    iter = pathlib.Path(CSV_SETTING["CSV_ORDER_DIR_PATH"]).glob(f"*{CSV_SETTING['CSV_ACCOUNT']}*")
    last = next(iter)
    for last in iter: pass
    file_date = re.match("[0-9]*",last.name).group()

    backup_csv_path = pathlib.Path(CSV_SETTING["CSV_BACKUP_DIR_PATH"]).absolute().joinpath(f"BACKUP_{file_date}_{CSV_SETTING['CSV_ACCOUNT']}.csv")
    if not backup_csv_path.exists():
        return

    tmp_df_order = pandas.read_csv(backup_csv_path)
    idx = tmp_df_order.loc[
                            (tmp_df_order["ContractID"] == getattr(req, "ContractID"))
                            & (tmp_df_order["Op1"] == getattr(req, "Op1"))
                            & (tmp_df_order["Op2"] == getattr(req, "Op2"))
                        ].index.values[0]
    
    tmp_df_order.loc[idx, "Num"] = left_vol
    tmp_df_order.to_csv(backup_csv_path, index=False)


async def save_df_pos(engine: ScriptEngine):
    while True:
        df_pos: pandas.DataFrame = engine.get_all_positions(use_df=True)
        if df_pos is not None:
            break
        await asyncio.sleep(3)

    df_pos['direction'] = df_pos["direction"].apply(lambda x : "Buy" if x == Direction.LONG else "Sell")
    df_pos.sort_values(["direction","symbol"],ascending=[True,True], inplace=True)
    df_pos = df_pos[["symbol","direction","volume"]]
    df_pos = df_pos[df_pos["volume"] != 0]

    print(df_pos)

    df_pos_path = pathlib.Path(CSV_SETTING['CSV_POS_DIR_PATH']).joinpath(f"{datetime.datetime.today().date().strftime('%Y%m%d')}_{CSV_SETTING['CSV_ACCOUNT']}_POS.csv")
    df_pos.to_csv(df_pos_path, index=False)
    

if __name__ == "__main__":
    asyncio.run(run_async())