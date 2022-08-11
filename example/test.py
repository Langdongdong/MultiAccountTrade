from dataclasses import dataclass
from datetime import datetime, time, timedelta

from pymongo import MongoClient
from base.database import MongoDatabase
from base.setting import settings
import re


if __name__ == "__main__":
    # 'sp2209.SHFE', 'CJ301.CZCE', 'TS2209.CFFEX', 'zn2209.SHFE', 'j2209.DCE', 'PM209.CZCE', 'ag2212.SHFE', 'rr2210.DCE', 
    # 'l2209.DCE', 'fu2301.SHFE', 'pp2209.DCE', 'FG301.CZCE', 'WH303.CZCE', 'pb2209.SHFE', 'sn2209.SHFE', 'au2212.SHFE', 
    # 'IM2208.CFFEX', 'bc2210.INE', 'cs2209.DCE', 'ss2209.SHFE', 'TA301.CZCE', 'p2209.DCE', 'c2301.DCE', 'RI209.CZCE', 
    # 'rb2210.SHFE', 'b2209.DCE', 'UR301.CZCE', 'al2209.SHFE', 'SR301.CZCE', 'y2301.DCE', 'IC2209.CFFEX', 'bu2212.SHFE', 
    # 'SM209.CZCE', 'eb2209.DCE', 'AP210.CZCE', 'OI209.CZCE', 'jm2209.DCE', 'sc2210.INE', 'lh2301.DCE', 'cu2209.SHFE', 
    # 'hc2210.SHFE', 'bb2212.DCE', 'JR301.CZCE', 'IH2209.CFFEX', 'CY209.CZCE', 'nr2210.INE', 'SF209.CZCE', 'wr2210.SHFE', 
    # 'SA301.CZCE', 'RS209.CZCE', 'i2301.DCE', 'ZC209.CZCE', 'a2209.DCE', 'RM301.CZCE', 'lu2211.INE', 'PK210.CZCE', 
    # 'v2209.DCE', 'ru2301.SHFE', 'ni2209.SHFE', 'pg2209.DCE', 'eg2209.DCE', 'LR305.CZCE', 'CF301.CZCE', 'T2209.CFFEX', 
    # 'IF2209.CFFEX', 'PF210.CZCE', 'TF2209.CFFEX', 'fb2209.DCE', 'm2301.DCE', 'jd2209.DCE', 'MA209.CZCE'
    mongo = MongoDatabase()
    data = mongo.load_bar_data("j2209", "20220811")
    for i in data: 
        print(i)
    print(len(data))


    # print(datetime.now() + timedelta(minutes=10))

