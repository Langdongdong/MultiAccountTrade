import sys
sys.path.append(".")

import re
from time import sleep

from jqdatasdk import is_auth, auth, get_dominant_future

from typing import Dict, Set, Tuple

from base.engine import BarEngine, MainEngine
from base.setting import settings
from vnpy.event import EventEngine
from vnpy.trader.constant import Product, Exchange
from vnpy_ctp import CtpGateway


configs = {
    "accounts": {
        "DDTEST0": {
            "用户名": "20177599",
            "密码": "19910703",
            "经纪商代码": "8080",
            "交易服务器": "27.115.78.182:41206",
            "行情服务器": "27.115.78.182:41214",
            "产品名称": "client_gwqtrader_v1.0.0",
            "授权编码": "L8WN410RZ28OJM3X",
            "gateway": CtpGateway
        },
        # "DDTEST1": {
        #     "用户名": "91600338",
        #     "密码": "dd027232",
        #     "经纪商代码": "5040",
        #     "交易服务器": "180.169.95.243:21205",
        #     "行情服务器": "220.248.39.103:21213",
        #     "产品名称": "client_miaowazy_1.0.0",
        #     "授权编码": "127WVB6B0IYUWYVK",
        #     "gateway": CtptestGateway
        # },
        # "DDTEST2": {
        #     "用户名": "99000072",
        #     "密码": "20202020",
        #     "经纪商代码": "5060",
        #     "交易服务器": "116.236.198.175:33437",
        #     "行情服务器": "116.236.198.175:33443",
        #     "产品名称": "client_ddtrader_v1.0.0",
        #     "授权编码": "ABCDEFGH12345678",
        #     "gateway": CtptestGateway
        # }
    },
}

def connect_jq() -> None:
    if not is_auth():
        auth('18301717901', 'JQzc666888')

def subscribe(main_engine: MainEngine, gateway_name: str = None) -> None:
    connect_jq()

    underlying_symbols: Dict[str, str] = {}
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

    n = 0
    for i in dominant_vt_symbols:
        n+=1
        print(n, main_engine.get_contract(i))
    
    main_engine.subscribe(dominant_vt_symbols, gateway_name)


if __name__ == "__main__":

    main_engine = MainEngine()
    # event_engine = EventEngine()

    # while True:
    #     if MainEngine.is_trading_time():
    #         break
    #     sleep(10)

    # bar_engine: BarEngine = main_engine.add_engine(BarEngine, is_persistence = False)

    main_engine.connect(configs.get("accounts"))

    # subscribe(main_engine)

    main_engine.subscribe(["rb2210.SHFE"])

    # print(MainEngine.is_night_trading_time())

    # if not MainEngine.is_trading_time():
    #     main_engine.df.to_csv("C:/Users/33292/Desktop/test.csv")
    #     main_engine.close()

    # gateway: CtpGateway = main_engine.get_all_gateways()[0]te
    # print("mdapi version - ",gateway.md_api.getApiVersion())
    # print("trading day - ", gateway.td_api.getTradingDay())
    # print("tdapi version - ",gateway.td_api.getApiVersion())

    # g = CtptestGateway(main_engine.event_engine, "dd")
    # print(g.md_api.getApiVersion())
    # while True:
    #     if not MainEngine.is_trading_time():
    #     #     for tick in main_engine.get_all_ticks():
    #     #         for k, v in tick.__dict__.items():
    #     #             main_engine.log(f"{k}:{v}")
    #     # sleep(1)
    #         break
    #     sleep(60)
        
    # main_engine.close()
    