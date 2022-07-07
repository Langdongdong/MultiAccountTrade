from ast import While
import re

from jqdatasdk import is_auth, auth, get_dominant_future

from typing import Dict, Set, Tuple

from base.engine import BarEngine, MainEngine
from base.setting import settings
from vnpy.trader.constant import Product, Exchange
from vnpy_ctp import CtpGateway


configs = {
    "accounts": {
        "DDTEST1": {
            "用户名": "083231",
            "密码": "wodenvshen199!",
            "经纪商代码": "9999",
            "交易服务器": "180.168.146.187:10130",
            "行情服务器": "180.168.146.187:10131",
            "产品名称": "simnow_client_test",
            "授权编码": "0000000000000000",
            "gateway": CtpGateway
        },
        # "DDTEST2": {
        #     "用户名": "201414",
        #     "密码": "wodenvshen199!",
        #     "经纪商代码": "9999",
        #     "交易服务器": "180.168.146.187:10130",
        #     "行情服务器": "180.168.146.187:10131",
        #     "产品名称": "simnow_client_test",
        #     "授权编码": "0000000000000000",
        #     "gateway": CtpGateway
        # }
    },
}

def connect_jq() -> None:
    if not is_auth():
        auth('18301717901', 'JQzc666888')

def subscribe(main_engine: MainEngine, gateway_name: str = None) -> None:
    connect_jq()

    underlying_symbols: Tuple[str] = ()
    dominant_vt_symbols: Set[str] = set()

    contracts = main_engine.get_all_contracts()
    for contract in contracts:
        if contract.product == Product.FUTURES:
            underlying_symbol = re.match("\D*", contract.symbol).group().upper()
            if not underlying_symbols.get(underlying_symbol):
                underlying_symbols[underlying_symbol] = contract.exchange

    for underlying_symbol, exchange in underlying_symbols.items():
        dominant_symbol: str = get_dominant_future(underlying_symbol).split('.')[0]

        if exchange == Exchange.CZCE:
            date = re.search("\d+", dominant_symbol).group()[-3:]
            dominant_vt_symbol = f"{underlying_symbol}{date}.{exchange.value}"
        elif exchange == Exchange.CFFEX:
            dominant_vt_symbol = f"{dominant_symbol}.{exchange.value}"
        else:
            dominant_vt_symbol = f"{dominant_symbol.lower()}.{exchange.value}"

        dominant_vt_symbols.add(dominant_vt_symbol)

    print(f"Subscribe {len(dominant_vt_symbols)} {dominant_vt_symbols}")
    
    main_engine.subscribe(dominant_vt_symbols, gateway_name)


def run_parent():
    pass

def run_child():
    pass

if __name__ == "__main__":
    is_tradeing: bool = False

    main_engine = MainEngine()
    bar_engine: BarEngine = main_engine.add_engine(BarEngine, period = 1, size = 1, is_persistence = False, collection_name = "")
    
    while True:
        if MainEngine.is_trading_time():
            is_tradeing = True
        else:
            is_tradeing = False
        
        if is_tradeing:
            

            main_engine.connect(configs.get("accounts"))
            subscribe(main_engine)

        


    # print(tick)
    # main_engine.close()