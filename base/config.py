from vnpy_ctp import CtpGateway
from vnpy_rohon import RohonGateway

# 180.168.146.187:10201
# 180.168.146.187:10211
# 180.168.146.187:10130
# 180.168.146.187:10131

# Set the accounts params.
ACCOUNT_SETTING = {
    "DDTEST1": 
    {
        "用户名": "083231",
        "密码": "wodenvshen199!",
        "经纪商代码": "9999",
        "交易服务器": "180.168.146.187:10201",
        "行情服务器": "180.168.146.187:10211",
        "产品名称": "simnow_client_test",
        "授权编码": "0000000000000000",
        "Gateway": "CtpGateway"
    },
    "DDTEST2": 
    {
        "用户名": "201414",
        "密码": "wodenvshen199!",
        "经纪商代码": "9999",
        "交易服务器": "180.168.146.187:10201",
        "行情服务器": "180.168.146.187:10211",
        "产品名称": "simnow_client_test",
        "授权编码": "0000000000000000",
        "Gateway": "CtpGateway"
    }
}

GATEWAY_SETTING = [CtpGateway, RohonGateway]

# Symbols which only can be traded in day time.
AM_SYMBOL_SETTING = {"UR","JD","AP","SM","SF","LH"}

# Set the file path params.
FILE_SETTING = {
    "ORDER_DIR_PATH": "Z:/position/TRADE/",
    "POSITION_DIR_PATH": "Z:/HOLD/",
    "BACKUP_DIR_PATH": "Z:/backup/",
    "LOG_DIR_PATH": "Z:/log/"
}

# Set the TWAP algo params.
SNIPER_SETTING = {
    "INTERVAL": 3,
    "HIT": 2,
    "LIMIT": 5
}