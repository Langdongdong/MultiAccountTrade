# encoding: UTF-8

"""
感谢Darwin Quant贡献的策略思路。
知乎专栏原文：https://zhuanlan.zhihu.com/p/24448511

策略逻辑：
1. 布林通道（信号）
2. CCI指标（过滤）
3. ATR指标（止损）



"""

from __future__ import division

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING, BUY_MARKET_PRICE, SELL_MARKET_PRICE, SHORT_MARKET_PRICE, \
    COVER_MARKET_PRICE
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate,
                                                     BarGenerator,
                                                     ArrayManager)

from datetime import datetime
import numpy  as np

DEBUG = False



########################################################################
class Abberation_adj55_00_min_day6(CtaTemplate):
    """基于布林通道的交易策略"""
    className = 'Abberation_adj55_00_min_day6'
    author = u'交易员'

    # 策略参数
    # 参数列表，保存了参数的数
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = []

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, strategy_setting, contract_dict, size,setting):
        """Constructor"""
        super(Abberation_adj55_00_min_day6, self).__init__(ctaEngine, contract_dict)

        # bg_func = {5:self.on5MinBar}
        bg_func ={}
        self.init_Array(ctaEngine, strategy_setting, contract_dict, size, bg_func,setting)

    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' % self.name)

        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onTick(self, tick,setting):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg[1][setting['Strategy_ID']][setting['sub_symbol']][setting['symbol']].updateTick(tick,setting)

    def onBar(self, bar, setting):

        """收到Bar推送（必须由用户继承实现）"""
        # 基于1分钟判断
        self.UpdateBGbar(bar, setting)
        self.UpdateData(setting)


        return self.UpdateFunc(bar,setting)

    # def on5MinBar(self, bar, setting):
    #
    #
    #     # 全撤之前发出的委托
    #
    #     # 保存K线数据
    #
    #     if self.is_satisfied_trade(bar,setting['Constants']['freq_1'], setting,self.bg):
    #
    #         am1 = self.GetArrayData(setting['Constants']['freq_1'], setting)
    #
    #         other =self.GetOther(False,setting) #如果想获取日线数据other数据，第一个参数为True
    #         entryPrice = other[0] if other is not None else None
    #
    #         bollUp, bollDown = am1.boll(setting['Parameters']['N'], setting['Parameters']['plus'])
    #         bollMa = am1.ma(setting['Parameters']['N'])
    #
    #         high50, low50 = am1.donchian_last(setting['Parameters']['len1'])
    #
    #         # 当前无仓位，发送开仓委托
    #         if setting['signal_dict']['flag'] == 0:
    #
    #             if bar.close > bollUp and bar.close > high50 :
    #                 self.setSignal(1, setting)
    #                 entryPrice= bar.close
    #                 #print('多头开仓'+str(bar.datetime)+str(setting['sub_symbol']))
    #
    #             elif bar.close < bollDown and bar.close < low50 :
    #                 self.setSignal( -1, setting)
    #                 entryPrice = bar.close
    #                 #print('空头开仓'+str(bar.datetime)+str(setting['sub_symbol']))
    #
    #         # 持有多头仓位
    #         elif setting['signal_dict']['flag'] > 0:
    #
    #             if bar.close < bollMa :
    #                 self.setSignal( 0, setting)
    #                 #print('多头平仓'+str(bar.datetime)+str(setting['sub_symbol']))
    #
    #         # 持有空头仓位
    #         elif setting['signal_dict']['flag'] < 0:
    #
    #             if bar.close > bollMa :
    #                 self.setSignal( 0, setting)
    #                 #print('空头平仓 '+str(bar.datetime)+str(setting['sub_symbol']))
    #
    #         # 同步数据到数据库
    #         self.saveSyncData()
    #         # 发出状态更新事件
    #         self.putEvent()
    #
    #         return [[bollUp,bollDown,bollMa,high50,low50],[entryPrice]]
    #
    #         #return [None,None]
    #     else:
    #         return [None,None]


    # ----------------------------------------------------------------------
    def onMinBar(self, bar, setting):

        # 全撤之前发出的委托

        # 保存K线数据

        if self.is_satisfied_trade(bar,setting['strategy_param']['backtest'].base_freq, setting,self.bg):
            am = self.GetArrayData(setting['Constants']['freq_1'], setting)
            am_day = self.GetArrayData(0, setting)
            if am_day.close[-60]==0:
                return [None,None]

            ma0=am_day.ma(setting['Parameters']['Nday'])
            # sd1 = am_day.atr(20)
            sd0=am_day.atr(20)
            ma2 = am_day.ma(setting['Parameters']['Nlen'])
            bollUp_day, bollDown_day = am_day.boll(20, 1.0)
            mad9 = am_day.ma(9)
            am_day = self.GetArrayData(setting['Constants']['freq_2'], setting)
            ma_60 = am_day.ma(60)
            sd1 = am_day.atr(20)
            # sd0=sd1
            ma5d = am_day.ma(5)
            other =self.GetOther(False,setting) #如果想获取日线数据other数据，第一个参数为True
            entryPrice = other[0] if other is not None else None
            ProtectStop = other[1] if other is not None else None
            code = other[2] if other is not None else None
            ProtectProfit = other[3] if other is not None else None
            entryLine = other[4] if other is not None else None
            close = am.close
            bollUp, bollDown = am_day.boll(60, 1.0)
            upr, dwn = am.boll(setting['Parameters']['N'], setting['Parameters']['plus'])
            bollMa = am.ma(setting['Parameters']['N'])
            ma10 = np.mean(close[-10:])
            ma20 = np.mean(close[-20:])
            ma50 = np.mean(close[-50:])
            maBefore50 = np.mean(close[-55:-5])
            ma4 = np.mean(close[-4:])
            ma9 = np.mean(close[-9:])
            ma18 = np.mean(close[-18:])
            slopp = ma50 - maBefore50
            conL = bar.close > max([ma0,bollUp,upr,ma_60,bollUp_day]) and am_day.close[-1] > am_day.close[-41] \
                   and bar.close < ma5d * (1 + 0.05)and slopp > 0 and (close[-1] > ma10 > ma20 > ma50 and close[-1] > ma4 > ma9 > ma18)
            conS = bar.close < min([ma0, ma2,bollDown,dwn,ma_60,bollDown_day]) and am_day.close[-1] < am_day.close[-41] \
                   and bar.close > ma5d * (1 - 0.05)and slopp < 0 and ( close[-1] < ma10 < ma20 < ma50 and close[-1] < ma4 < ma9 < ma18)
            # exitL = bar.close <mad9 < ma2
            # exitS = bar.close >mad9 > ma2
            # exitL = bar.close < ma2
            # exitS = bar.close  > ma2
            # exitL = bar.close < min(ma_60,bollMa,ma2)
            # exitS = bar.close  > max(ma_60,bollMa,ma2)
            # exitL = bar.close < min(ma_60,bollMa)
            # exitS = bar.close  > max(ma_60,bollMa)
            exitL = bar.close < min(mad9,ma2,bollMa)
            exitS = bar.close  > max(mad9,ma2,bollMa)
            pls = 5
            # 当前无仓位，发送开仓委托
            if setting['signal_dict']['flag'] != 0:
                if  am.code > code:
                    dp = am.close[-1] - entryPrice
                    entryPrice += dp
                    ProtectStop += dp
                    ProtectProfit+=dp
                    code = am.code
                    entryLine+=dp
            if setting['signal_dict']['flag'] == 0:

                if conL:
                    self.setSignal(1, setting)
                    entryPrice= bar.close
                    ProtectProfit=entryPrice+3*pls*sd0
                    ProtectStop=entryPrice-pls*sd0
                    code = am.code
                    entryLine = bar.close
                    print('多头开仓'+str(bar.datetime)+ "下单标的" + str(am.code))

                elif conS:
                    self.setSignal( -1, setting)
                    entryPrice = bar.close
                    code = am.code
                    ProtectProfit=entryPrice-3*pls*sd0
                    ProtectStop=entryPrice+pls*sd0
                    entryLine = bar.close
                    print('空头开仓'+str(bar.datetime)+ "下单标的" + str(am.code))

            # 持有多头仓位
            elif setting['signal_dict']['flag'] > 0:
                entryLine = max(entryLine, bar.close)
                TrailStop =entryLine- pls * sd0
                if TrailStop >= ProtectStop:
                    ProtectStop = TrailStop
                else:
                    ProtectStop = ProtectStop
                if exitL or bar.close <=ProtectStop or (bar.close >ma5d*(1+0.1) and ~conL):
                    self.setSignal( 0, setting)
                    print('多头平仓'+str(bar.datetime)+ "下单标的" + str(am.code))

            # 持有空头仓位
            elif setting['signal_dict']['flag'] < 0:
                entryLine = min(entryLine, bar.close)
                TrailStop = entryLine + pls * sd0
                if TrailStop <= ProtectStop:
                    ProtectStop = TrailStop
                else:
                    ProtectStop = ProtectStop
                if exitS or bar.close >= ProtectStop or (bar.close < ma5d * (1 - 0.1) and ~conS):
                    self.setSignal(0, setting)
                    print('空头平仓 '+str(bar.datetime)+ "下单标的" + str(am.code))

            # 同步数据到数据库
            self.saveSyncData()
            # 发出状态更新事件
            self.putEvent()

            return [[bollUp,bollDown,sd0,sd1],[entryPrice,ProtectStop,code,ProtectProfit,entryLine]]

            # return [None,None]

        else:
            return [None,None]

        # ----------------------------------------------------------------------

    def onDayBar(self, bar, setting):

        # 全撤之前发出的委托


        """日K线推送"""
        if self.is_satisfied_trade(bar,0, setting,self.bg):
            pass

        # 同步数据到数据库
        self.saveSyncData()

        # 发出状态更新事件
        self.putEvent()
        return [None,None]

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass
