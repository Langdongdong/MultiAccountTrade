import re
from threading import main_thread

from jqdatasdk import is_auth, auth, get_dominant_future

from typing import Set

from base.engine import BarEngine, MainEngine
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

    underlying_symbols: Set[str] = set()
    dominant_symbols: Set[str] = set()

    contracts = main_engine.get_all_contracts()
    for contract in contracts:
        underlying_symbol = re.match("\D*", contract.symbol).group().upper()
        underlying_symbols.add(underlying_symbol)

    print(underlying_symbols, len(underlying_symbols))

    for underlying_symbol in underlying_symbols:
        dominant_symbol: str = get_dominant_future(underlying_symbol).split('.')[0]
        dominant_symbols.add(dominant_symbol)

    print(dominant_symbols, len(dominant_symbols))

    for contract in contracts:
        if contract.symbol.upper() == 

    # print(len(dominant_contracts),dominant_contracts)
    # main_engine.subscribe(dominant_contracts, gateway_name)

if __name__ == "__main__":
    main_engine = MainEngine()
    # bar_engine: BarEngine = main_engine.add_engine(BarEngine, period = 1, size = 1, is_persistence = True)

    main_engine.connect(configs.get("accounts"))
    subscribe(main_engine)
    # auth('18301717901', 'JQzc666888')
    # # if not get_dominant_future("PK"):
    # #     print(1)
    # print(get_dominant_future("PK"))
