import datetime
import backtrader as bt
import pandas as pd
import tushare as ts

# 简单测试脚本：初始化 Tushare 接口并获取基金基础数据。
pro = ts.pro_api()
df = pro.fund_basic(market='E')
print(df.head(5))