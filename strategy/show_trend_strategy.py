"""策略层：定义用于展示行情走势的策略。"""

import backtrader as bt


class ShowTrendStrategy(bt.Strategy):
    """仅用于展示价格走势，不进行真实交易。"""

    def next(self):
        # Backtrader 每根 K 线都会调用一次 next()
        # 这里不写交易逻辑，只是让数据正常运行并显示图表
        pass
