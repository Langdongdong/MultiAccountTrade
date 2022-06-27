from datetime import datetime
from base.database import MongoDatabase

from base.engine import MainEngine, BarEngine
from vnpy_ctp import CtpGateway
import time

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

if __name__ == "__main__":
   
    engine = MainEngine()
    engine.connect(configs.get("accounts"))

    engine.subscribe( {"rb2210.SHFE"}, engine.get_all_gateway_names()[0])

    bar_engine: BarEngine = engine.add_engine(BarEngine, period = 1, size = 1, is_persistence = True)
