import re

from typing import Dict, Set

from base.engine import CtpEngine
from base.setting import SETTINGS

from vnpy.trader.constant import Product, Exchange

from jqdatasdk import auth, get_dominant_future, is_auth

def connect() -> None:
    while True:
        if is_auth():
            return
        else:
            auth(SETTINGS["joinquant.username"], SETTINGS["joinquant.password"])

def get_dominant_symbols(ctp_engine: CtpEngine) -> Set[str]:
    connect()

    underlying_symbol_exchange_map: Dict[str, str] = {}

    contracts = ctp_engine.get_all_contracts()
    if contracts:
        for contract in contracts:
            if contract.product == Product.FUTURES:
                underlying_symbol = re.match("\D*", contract.symbol).group().upper()

                if not underlying_symbol_exchange_map.get(underlying_symbol):
                    underlying_symbol_exchange_map[underlying_symbol] = contract.exchange

    dominant_symbols: Set[str] = set()
    for underlying_symbol, exchange in underlying_symbol_exchange_map.items():
        dominant_symbol: str = get_dominant_future(underlying_symbol).split('.')[0]

        if exchange == Exchange.CZCE:
            date = re.search("\d+", dominant_symbol).group()[-3:]
            dominant_symbol = f"{underlying_symbol}{date}"
        elif exchange == Exchange.CFFEX:
            dominant_symbol = f"{dominant_symbol}"
        else: # DCE, INE, SHFE
            dominant_symbol = f"{dominant_symbol.lower()}"

        dominant_symbols.add(dominant_symbol)

    ctp_engine.write_log(f"Get {len(dominant_symbols)} dominant symbols.")

    return dominant_symbols