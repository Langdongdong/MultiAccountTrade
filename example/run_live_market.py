import sys

sys.path.append('.')

import re

from datetime import datetime
from time import sleep
from typing import Dict, Set
from jqdatasdk import is_auth, auth, get_dominant_future

from base.engine import CtpEngine
from base.setting import ACCOUNTS

from vnpy.event import EventEngine
from vnpy.trader.constant import Product, Exchange
from vnpy_ctp import CtpGateway

def connect_jq() -> None:
    if not is_auth():
        auth('18301717901', 'JQzc666888')

def subscribe(ctp_engine: CtpEngine, gateway_name: str = "") -> None:
    connect_jq()

    underlying_symbols: Dict[str, str] = {}
    dominant_symbols: Set[str] = set()

    contracts = ctp_engine.get_all_contracts()
    for contract in contracts:
        if contract.product == Product.FUTURES:
            underlying_symbol = re.match("\D*", contract.symbol).group().upper()
            if not underlying_symbols.get(underlying_symbol):
                underlying_symbols[underlying_symbol] = contract.exchange

    for underlying_symbol, exchange in underlying_symbols.items():
        dominant_symbol: str = get_dominant_future(underlying_symbol).split('.')[0]

        if exchange == Exchange.CZCE:
            date = re.search("\d+", dominant_symbol).group()[-3:]
            dominant_symbol = f"{underlying_symbol}{date}"
        elif exchange == Exchange.CFFEX:
            dominant_symbol = f"{dominant_symbol}"
        else:
            dominant_symbol = f"{dominant_symbol.lower()}"

        contract = ctp_engine.get_contract(dominant_symbol)
        if contract:
            dominant_symbols.add(contract.symbol)

    print(f"Subscribe {len(dominant_symbols)}")

    # for i in dominant_symbols:
    #     print(ctp_engine.get_contract(i))
    
    ctp_engine.subscribe(dominant_symbols, gateway_name)


if __name__ == "__main__":

    while True:
        if CtpEngine.is_trading_time():
            break

    ctp_engine = CtpEngine()
 
    ctp_engine.connect_all(ACCOUNTS)

    subscribe(ctp_engine) 

    while True:
        sleep(60)
        
        if not CtpEngine.is_trading_time():
            break
    #     print(datetime.now())
    #     print("bar count", len(bar_engine.bar_generator.bars))
    #     print(bar_engine.bar_generator.bars)

    #     print(len(bar_engine.bar_generator.last_ticks))
    #     print(bar_engine.bar_generator.last_ticks)

    #     print(len(ctp_engine.ticks))
    #     # print(ctp_engine.ticks)

    #     data: pandas.DataFrame = ctp_engine.get_all_ticks(True)
    #     data.to_csv("D:/test.csv")
    
        
    ctp_engine.close()
    