from constant import OrderMode
from vnpy.trader.constant import Exchange

class OrderRequest:
    def __init__(self, ContractID: str, Op1: str, Op2: str, Num: float) -> None:
        self.ContractID = ContractID
        self.Op1 = Op1
        self.Op2 = Op2
        self.volume = Num
        self.vt_symbol = self.convert_to_vt_symbol(self.ContractID)
        self.order_mode = self.convert_to_vt_order_mode(self.Op1, self.Op2)

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