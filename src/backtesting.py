"""导入常用模块"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from jqdata import *
from pylab import mpl
import seaborn as sns

mpl.rcParams['font.sans-serif'] = ['FangSong'] # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题


"""账户类"""
class Context:
    def __init__(self):
        self.cash = self.Cash = 100000 # 默认初始资金
        self.base = '000300.XSHG' # 默认参考基准
        self.position = {} # 持仓
        self.universe = [] # 标的池
        self.current_dt = '2016-01-01'
        self.start_date = '2016-01-01' # 默认交易开始时间
        self.end_date = '2016-12-31' # 默认交易结束时间
        self.total_value = 0 # 总价值
        self.trade_history = [] # 交易历史记录
        self.day_value = [] # 日收益记录
        self.trade_days = 0

    # 记录每日收益
    def write_ratio(self, security, date):
        the_value = self.cash
        for s in self.position.keys():
            # 计算相对于上个交易日的涨跌幅度
            price = get_price(s,
                              end_date=date,
                              frequency='daily',
                              fields=['close'],
                              skip_paused=False,
                              fq='pre',
                              count=10)['close']

            value = self.position[s]['count']*price[-1]
            the_value += value
        self.day_value.append({'date':date, 'value':the_value})
        


"""下单类"""
class Order:
    context = Context()

    def __init__(self, context):
        self.context = context

    # 交易函数，买入与卖出
    def buy(self, security, price, count):
        if price * count > self.context.cash:
            print('资金不足，请调整数量！')
            return

        if security in self.context.position.keys():
            print('暂不支持重复下单！')
            return

        _total_value = price * count
        self.context.cash -= _total_value
        _positon = {'security': security,
                    'price': price,
                    'count': count,
                    'date': self.context.current_dt,
                    'type': 'buy',
                    'hold_value': price * count,
                    'available_cash': self.context.cash}
        self.context.trade_history.append(_positon)
        self.context.total_value = self.context.cash + _total_value
        self.context.position[security] = _positon

    def sell(self, security, price, count):
        if security not in self.context.position.keys():
            print('持仓中不包含标的{}，无法交易！'.format(security))
            return

        if count != self.context.position[security]['count']:
            print('这支持分批卖出，请输入全部数量！')
            return

        _total_value = price * count
        self.context.cash += _total_value
        _positon = {'security': security,
                    'price': price,
                    'count': count,
                    'date': self.context.current_dt,
                    'type': 'sell',
                    'hold_value': price * count,
                    'available_cash': self.context.cash}
        self.context.trade_history.append(_positon)
        self.context.total_value = self.context.cash  # ?
        del self.context.position[security]


"""交易类"""
class Trade:
    def __init__(self, context, order):
        self.context = context # 账户
        self.order = order # 下单对象
        self.result = {} # 回测后的评估指标
        self.price = None # 价格缓存
        self.maxdown_point = [] # 记录最大回撤点位


    # 策略回测
    def trade(self, func, show=True, log=False):
        time_start = datetime.datetime.now()
        self.price = get_price(security=self.context.base,
                              start_date=self.context.start_date,
                              end_date=self.context.end_date,
                              frequency='daily',
                              fields=None,
                              skip_paused=False,
                              fq='pre')
        close = self.price['close']
        for i in range(0, len(close)):
            self.context.current_dt = close.index[i]
            self.context.trade_days = i+1
            func(self.context, self.order)
            self.context.write_ratio(self.context.universe[0], self.context.current_dt)
        self.get_result()
        time_end = datetime.datetime.now()
        if log:
            print('End Time : {0}, Elapsed Time: {1}'.format(datetime.datetime.now(), time_end - time_start))
        if show:
            self.show_ratio()

    # 查询交易记录详情
    def get_trade_detail(self):
        _df = pd.DataFrame(self.context.trade_history,
                           columns=['date',
                                    'security',
                                    'type',
                                    'price',
                                    'count',
                                    'hold_value',
                                    'available_cash'])
        _df.rename(columns={'date': '时间',
                            'security': '标的',
                            'type': '交易类型',
                            'price': '交易价格',
                            'count': '交易数量',
                            'hold_value': '持仓价值',
                            'available_cash': '可用资金'}, inplace=True)
        return _df

    """评估指标"""

    # 策略收益
    def get_absolute_return(self):
        _cash = pd.DataFrame(self.context.day_value)['value'].iloc[-1]
        return (_cash - self.context.Cash) / self.context.Cash

    """
    年化收益率公式为：
    年化收收益率 = （总收益 + 1）** (365.25/天数) -1  【计算自然日/年化收益率】
    年化收收益率 = （总收益 + 1）** (250/天数) -1  【计算交易日/年化收益率】
    """
    # 策略年化收益率
    def get_annualized_return(self):
        _cash = pd.DataFrame(self.context.day_value)['value'].iloc[-1]
        ratio = (_cash - self.context.Cash) / self.context.Cash
        return_value = (1 + ratio) ** (252 / len(self.context.day_value)) - 1
        return return_value

    # 基准收益
    def get_benchmark_return(self):
        ben_data = self.price
        benchmark_return = (ben_data['close'][-1] - ben_data['open'][0]) / ben_data['open'][0]
        return benchmark_return
    
    # 基准年化收益率
    def get_anbenchmark_return(self):
        anbenchmark_return = (1 + self.get_benchmark_return()) ** (250 / len(self.context.day_value)) - 1
        return anbenchmark_return
    
    # 计算盈亏比
    def get_profit_loss_than(self):
        _df = pd.DataFrame(self.context.trade_history)
        if _df.shape[0] <= 0:
            return 0
        _df['total_value'] = _df['available_cash'] + _df['hold_value']
        _sell = _df[_df['type'] == 'sell']['available_cash']
        _trade_count = _df[_df['type'] == 'sell'].shape[0]
        _buy = _df[_df['type'] == 'buy']['total_value'][0:_trade_count]
        ratio = np.array(_sell) - np.array(_buy)
        return abs(ratio[ratio > 0].sum()/ratio[ratio < 0].sum())

    # 计算交易次数
    def get_trade_count(self):
        _df = pd.DataFrame(self.context.trade_history)
        if _df.shape[0] <= 0:
            return 0
        return len(_df[_df['type'] == 'sell'].index)

    # 计算胜率
    def get_wine_rate(self):
        _df = pd.DataFrame(self.context.trade_history)
        if _df.shape[0] <= 0:
            return 0
        _df['total_value'] = _df['available_cash'] + _df['hold_value']
        _sell = _df[_df['type'] == 'sell']['available_cash']
        _trade_count = _df[_df['type'] == 'sell'].shape[0]
        _buy = _df[_df['type'] == 'buy']['total_value'][0:_trade_count]
        ratio = np.array(_sell) - np.array(_buy)
        return len(ratio[ratio > 0])/len(ratio)
    
    # 夏普比率
    def get_sharpe(self):
        _df = pd.DataFrame(self.context.day_value)
        if _df.shape[0] <= 0:
            return 0
        std = ((_df['value'] - self.context.Cash) / self.context.Cash).std()
        if std == 0:
            return 0
        return (self.get_annualized_return() - 0.02) * np.sqrt(252) / std
    
    # beta
    def get_beta(self):
        ben_data = self.price
        ben_data['income'] = ben_data['close'].shift(1)
        ben_data['income1'] = ben_data['close'].astype(float) - ben_data['income'].astype(float)
        ben_data['income2'] = ben_data['income1'] / ben_data['income']
        ben_data_income = np.array(list(ben_data['income2'].dropna()))

        # 策略每日收益
        _df = pd.DataFrame(self.context.day_value)
        _df['income'] = _df['value'].shift(1)
        _df['income1'] = _df['value'].astype(float) - _df['income'].astype(float)
        _df['income2'] = _df['income1'] / _df['income'] 
        _df_income = np.array(list(_df['income2'].dropna()))

        x = np.cov(ben_data_income, _df_income)
        y = np.var(ben_data_income)
        # 获取beta值
        x_y_data = round(x[0][1]/y, 4)
        return x_y_data
            
    # alpha
    def get_alpha(self):
        alpha_data = self.get_annualized_return() - (0.04 + self.get_beta() * (self.get_anbenchmark_return() - 0.04))
        return alpha_data
    
    """
    最大回撤计算方式：
    在选定周期内任一历史点往后推，净值下降到最低点时的收益率回撤幅度的最大值。
    计算方式有两种：
    1. 往前计算，首先计算出每天和前面最高点比的最大回撤：1 - 当天值 / 前面的最大值，然后计算出这些数据里最大的值。
    2. 往二计算，首先计算出每天和后面最低点比较的最大回撤：1 - 后面的最小值 / 当天值，然后计算出这些数据里最大值。
    """
    # 最大回撤
    def get_maxdown(self):
        _df = pd.DataFrame(self.context.day_value)
        return_list = _df['value']
        i = np.argmax((np.maximum.accumulate(return_list) - return_list) / np.maximum.accumulate(return_list))  # 结束位置
        if i == 0:
            return 0
        j = np.argmax(return_list[:i])  # 开始位置
        
        # 记录最大回撤的点位
        self.maxdown_point.append(_df.iloc[j])
        self.maxdown_point.append(_df.iloc[i])

        return (return_list[j] - return_list[i]) / (return_list[j])
    
    # 总结回测信息
    def get_result(self):
        _dic = {'基准收益':round(self.get_benchmark_return(), 4),
                '策略收益':round(self.get_absolute_return(), 4),
                '年化收益':round(self.get_annualized_return(), 4),
                '最大回撤':round(self.get_maxdown(), 4),
                '夏普比率':round(self.get_sharpe(), 4),
                '盈亏比':round(self.get_profit_loss_than(), 4),
                '胜率':round(self.get_wine_rate(), 4),
                '交易次数':self.get_trade_count(),
                'beta':self.get_beta(),
                'alpha':self.get_alpha(),
                '回测时间':self.context.start_date+'~'+self.context.end_date}
        self.result = _dic
        return _dic
    
    
    # 报表展示
    @staticmethod
    def show_result(index_name, index_list, trade_list):
        _list = []
        for i in range(0, len(trade_list)):
            _trade = trade_list[i]
            _dic = _trade.result
            _dic[index_name] = index_list[i]
            _list.append(_trade.result)
        _df = pd.DataFrame(_list)
        _df = _df.set_index(index_name)
        _df = _df.sort_values(by=['年化收益','最大回撤', 'alpha', '夏普比率', 'beta', '胜率'], 
                   ascending=(False, True, False, False, True, False))
        return _df


    """图例展示，所有的评估皆以收盘价为基准""" 
    # 展示收益率曲线
    def show_ratio(self, w=20, h=7):
        sns.set()
        _price = self.price
        
        # 大盘相对涨幅
        start_price = _price['close'].iloc[0]
        _price['dapan_ratio'] = (_price['close'] - start_price) / start_price

        # 策略的相对涨幅
        _day_price = pd.DataFrame(self.context.day_value)
        _day_price['trade_ratio'] = (_day_price['value'] - self.context.Cash) / self.context.Cash

        plt.figure(figsize=(w, h))
        # 收益曲线
        plt.plot(_price.index, _price['dapan_ratio'], linewidth = '2', color='#FF4500')
        plt.plot(_day_price['date'], _day_price['trade_ratio'], linewidth = '2', color='#1E90FF')
        
        # 回撤点位
        x_list = [date['date'] for date in self.maxdown_point]
        y_list = [(date['value'] - self.context.Cash) / self.context.Cash for date in self.maxdown_point]
        plt.scatter(x_list, y_list, c='g',linewidths=7, marker='o')

        # 评估指标
        plt.title('Benchmark Returns {0}|Total Returns {1}|Annualized Returns {2}|Max Drawdown {3}|RunTime {4}'.format(
            self.result['基准收益'],
            self.result['策略收益'],
            self.result['年化收益'],
            self.result['最大回撤'],
            self.result['回测时间']), fontsize=16)
        plt.grid(True)
        plt.legend(['Benchmark Returns', 'Total Returns'], loc=2, fontsize=14)
        plt.show()

    # 查看对比图
    @staticmethod
    def show_ratio_compare(index_name, index_list, trade_list, r=2, c=2, w=16, h=9):
        """指标名，指标列表，交易对象列表，绘图行数，绘图列数"""
        sns.set()
        
        # 计算一个子图的宽
        width = w / c
        # 计算一个子图的高
        high = width*0.56

        figure,ax = plt.subplots(r, c, figsize=(w,(high+0.5)*r))

        j = 0
        for _ax in ax:
            for __ax in _ax:
                trade = trade_list[j]
                _price = trade.price
                # 大盘相对涨幅
                start_price = _price['close'].iloc[0]
                _price['dapan_ratio'] = (_price['close'] - start_price) / start_price
                # 策略的相对涨幅
                _day_price = pd.DataFrame(trade.context.day_value)
                _day_price['trade_ratio'] = (_day_price['value'] - trade.context.Cash) / trade.context.Cash

                __ax.plot(_price.index, _price['dapan_ratio'], color='#FF4500')
                __ax.plot(_day_price['date'], _day_price['trade_ratio'], color='#1E90FF')
                __ax.set_title('{0}={1}'.format(index_name,index_list[j],), fontsize=14)
                j += 1
        plt.show()
        
    @staticmethod
    def show_all_ratio(name , ma_list, trade_list, w=16, h=9):
        sns.set()
        
        _legend = [name+'='+str(_ma) for _ma in ma_list]
        plt.figure(figsize=(w, h))
        for trade in trade_list:
            _day_price = pd.DataFrame(trade.context.day_value)
            _day_price['trade_ratio'] = (_day_price['value'] - trade.context.Cash) / trade.context.Cash
            plt.plot(_day_price['date'], _day_price['trade_ratio'])
        plt.legend(_legend)
        plt.show()
        
class Picture:
    """展示指标图"""
    pass

class Model:
    """交易模型，保存量化后的参数"""
    pass