from dataclasses import dataclass
from datetime import datetime, time, timedelta

from pymongo import MongoClient
from base.database import MongoDatabase
from base.setting import settings
import re


if __name__ == "__main__":
    # 'RM301.CZCE', 'eg2209.DCE', 'FG209.CZCE', 'bb2207.DCE', 'pp2209.DCE', 'WH303.CZCE', 'y2209.DCE', 'SA209.CZCE', 'nr2209.INE', 
    # 'j2209.DCE', 'pg2208.DCE', 'TA209.CZCE', 'T2209.CFFEX', 'AP210.CZCE', 'bu2209.SHFE', 'SF209.CZCE', 'eb2208.DCE', 'cu2208.SHFE', 
    # 'm2209.DCE', 'ru2209.SHFE', 'a2209.DCE', 'PM209.CZCE', 'lh2209.DCE', 'v2209.DCE', 'l2209.DCE', 'sc2209.INE', 'CJ209.CZCE', 'c2209.DCE', 
    # 'ni2208.SHFE', 'IH2207.CFFEX', 'fb2209.DCE', 'TF2209.CFFEX', 'ag2212.SHFE', 'jd2209.DCE', 'JR301.CZCE', 'bc2209.INE', 'b2209.DCE', 
    # 'sp2209.SHFE', 'cs2209.DCE', 'CF209.CZCE', 'SR209.CZCE', 'SM209.CZCE', 'sn2208.SHFE', 'UR209.CZCE', 'zn2208.SHFE', 'rr2209.DCE', 
    # 'p2209.DCE', 'wr2210.SHFE', 'hc2210.SHFE', 'i2209.DCE', 'jm2209.DCE', 'IF2207.CFFEX', 'IC2207.CFFEX', 'PF210.CZCE', 'lu2210.INE', 
    # 'OI209.CZCE', 'RS209.CZCE', 'TS2209.CFFEX', 'ZC209.CZCE', 'rb2210.SHFE', 'PK210.CZCE', 'CY209.CZCE', 'al2208.SHFE', 'fu2209.SHFE', 
    # 'MA209.CZCE', 'LR207.CZCE', 'RI207.CZCE', 'au2212.SHFE', 'pb2208.SHFE', 'ss2208.SHFE'
    mongo = MongoDatabase()
    data = mongo.load_bar_data("rb2210", "20220810")
    for i in data: 
        print(i)
    print(len(data))


    # print(datetime.now() + timedelta(minutes=10))

