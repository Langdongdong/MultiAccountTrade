import re

from typing import Dict, Set

from base.engine import CtpEngine
from base.setting import SETTINGS

from vnpy.trader.constant import Product, Exchange

from jqdatasdk import auth, get_dominant_future, is_auth

def connect() -> None:
    if not is_auth():
        auth(SETTINGS["joinquant.username"], SETTINGS["joinquant.password"])

def get_dominant_symbols(ctp_engine: CtpEngine) -> Set[str]:
    connect()

    underlying_symbols: Set[str] = set()


    contracts = ctp_engine.get_all_contracts()
    if contracts:
        for contract in contracts:
            if contract.product == Product.FUTURES:
                underlying_symbols = re.match("\D*", contract.symbol).group().upper()
