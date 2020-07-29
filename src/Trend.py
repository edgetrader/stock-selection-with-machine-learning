#!/usr/bin/env python
# coding: utf-8

# In[3]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import talib as tb
from jqdata import *
import datetime
import seaborn as sns
sns.set()


# In[4]:


def get_kama(security, end_date=None, start_date=None, count=None, windows=21):
    if start_date != None and count != None:
        return Exception('start_date and count can not be used at the same time！')
    
    price = None
    if end_date != None and start_date != None:
        price = get_price(security, end_date=end_date, start_date=start_date)
    elif end_date != None and count != None:
        price = get_price(security, end_date=end_date, count=count)
        
    kama = tb.KAMA(price.close, timeperiod=windows)
    return kama


# In[5]:


def show_kama(security, data, up=0.0006, down=-0.0009):
    # 状态标记
    start_date = data.index[0]
    end_date = data.index[-1]
    check_index = 0
    state = 0
    
    # 数据整合
    price = get_price(security, start_date=start_date, end_date=end_date)
    price['kama'] = data
    price['log_rate'] = np.log(price['kama'] / price['kama'].shift(1))
    price.dropna(inplace=True)
    
    # 状态检测 
    def check_state(i):
        log_rate = price['log_rate'][i]

        _state = 0
        if log_rate >= up:
            _state = 1
        elif log_rate <= down:
            _state = -1
        else:
            _state = 0
        return _state
    
    # 线条展示
    def show_line(i):
        end_ind = price.index[i - 1]
        show_data = price.loc[check_index: end_ind, :]

        color = 'r'
        if state == 1:
            color = 'r'
        elif state == -1:
            color = 'g'
        else:
            color = 'y'

        show_data['kama'].plot(ax=ax, c=color, linewidth=4.0, alpha=0.9)
        return color
            
    fig, ax = plt.subplots(figsize=(18, 9))
    for i in range(price.shape[0]):
        if i == 0:  # 初次运行
            check_index = price.index[0]
            state = 0
            continue
        
        # 按波动范围切分
        _state = check_state(i)
        if _state != state:
            show_line(i)
            check_index = price.index[i - 1]
            state = _state
        # 最后一批数据
        if i == range(price.shape[0])[-1]:
            _state = check_state(i)
            state = _state
            color = show_line(i + 1)
            # 最后一天的位置画一个大圆点
            plt.scatter(x=price.index[-1], y=price['kama'][-1], 
                        c=color, linewidth=8.0, alpha=0.7)
            title = ''
            if state == 1:
                title = 'Current trend: long'
            elif state == -1:
                title = 'Current trend: short'
            else:
                title = 'Current trend: wait and see'
            plt.title(title)
    
    plt.scatter(x=price.index, y=price['close'], alpha=0.5)
    plt.show()


# In[6]:


# 计算近n年的波动率数据
def get_up_down(security, end_date, kama_windows=21):
    start_date = get_security_info(security).start_date
    price = get_price(security, start_date=start_date, end_date=end_date)
    price['kama'] = tb.KAMA(price.close, timeperiod=kama_windows)
    price['log_rate'] = np.log(price['kama'] / price['kama'].shift(1))
    price.dropna(inplace=True)
    describe = price.describe()
    return describe['log_rate']['25%'], describe['log_rate']['75%']


# In[7]:
def monitor(security='000300.XSHG', windows=21, count=244):
    # 交易时间
    trade_date = get_trade_days(end_date=datetime.datetime.now(), count=windows + count)
    last_day = trade_date[-2]
    if datetime.datetime.now().hour > 17:
        last_day = trade_date[-1]

    # 窗口与波动参数
    count = count + windows
    up_down = get_up_down(security, last_day, kama_windows=windows)
    up = up_down[1]
    down = up_down[0]

    # 趋势计算与展示
    KAMA = get_kama(security, end_date=last_day, count=count, windows=windows)
    show_kama(security, KAMA, up=up, down=down)




