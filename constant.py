import enum, datetime
from vnpy.trader.constant import Exchange

DAY_START = datetime.time(8, 45)
DAY_END = datetime.time(15, 0)

NIGHT_START = datetime.time(20, 45)
NIGHT_END = datetime.time(2, 45)


SYMBOL_AM = ["UR","JD","AP","SM","SF","LH"]


TWAP_SETTING = {
    "TIME": 60, 
    "INTERVAL" : 30
}

# 180.168.146.187:10201
# 180.168.146.187:10211
# 180.168.146.187:10130
# 180.168.146.187:10131
CTP_SETTING = {
    "用户名": "083231",
    "密码": "wodenvshen199!",
    "经纪商代码": "9999",
    "交易服务器": "180.168.146.187:10201",
    "行情服务器": "180.168.146.187:10211",
    "产品名称": "0000000000000000",
    "授权编码": "0000000000000000",
}


CSV_SETTING = {
    "CSV_ORDER_DIR_PATH" : "Z:/position/TRADE/",
    "CSV_POS_DIR_PATH" : "Z:/HOLD/",
    "CSV_BACKUP_DIR_PATH" : "D:/vnpy_trade/BACKUP/",
    "CSV_ACCOUNT" : "DDTEST",
}


TRADE_TIME_SETTING = {
    "DAY_START": datetime.time(9, 0),
    "DAT_END": datetime.time(15, 0),
    "NIGHT_START": datetime.time(21, 0),
    "NIGHT_END": datetime.time(23, 0)
}


class OrderMode(enum.Enum):
    BUY = "OPEN_BUY"
    SELL = "CLOSE_SELL"
    SHORT = "OPEN_SELL"
    COVER = "CLOSE_BUY"


class OrderRequest:
    def __init__(self, ContractID: str, Op1: str, Op2: str, Num: float) -> None:
        self.vt_symbol = self.convert_to_vt_symbol(ContractID)
        self.order_mode = self.convert_to_vt_order_mode(Op1, Op2)
        self.volume = Num

    @classmethod
    def convert_to_vt_symbol(self, symbol: str) -> str:
        spl = symbol.split(".")
        pre = spl[0].lower()
        suf = spl[1]

        if suf == "CZC":
            pre = pre.upper()
            suf = Exchange.CZCE.value

        elif suf == "SHF":
            suf = Exchange.SHFE.value

        return f"{pre}.{suf}"

    @classmethod
    def convert_to_symbol(self, vt_symbol: str) -> str:
        spl = vt_symbol.split(".")
        pre = spl[0].upper()
        suf = spl[1]

        if suf == Exchange.CZCE.value:
            suf = "CZC"
        elif suf == Exchange.SHFE.value:
            suf = "SHF"

        return f"{pre}.{suf}"

    @classmethod
    def convert_to_vt_order_mode(self, Op1: str, Op2: str) -> OrderMode:
        if Op1 == "Open":
            if Op2 == "Buy":
                return OrderMode.BUY
            else:
                return OrderMode.SHORT
        else:
            if Op2 == "Buy":
                return OrderMode.COVER
            else:
                return OrderMode.SELL

    @classmethod
    def convert_to_order_mode(self, order_mode: OrderMode) -> tuple:
        if order_mode == OrderMode.BUY:
            return "Open", "Buy"
        elif order_mode == OrderMode.SHORT:
            return "Open", "Sell"
        elif order_mode == OrderMode.COVER:
            return "Close", "Buy"
        elif order_mode == OrderMode.SELL:
            return "Close", "Sell"