
import backtrader as bt

# Strategy 结构说明：
# 1. 参数定义（params）：用于集中管理策略可调参数。
# 2. 初始化方法（__init__）：创建指标、保存数据引用、初始化状态变量。
# 3. 下一个数据点处理（next）：核心交易逻辑，在每根 K 线上决定买卖/持仓行为。
# 4. 订单通知（notify_order）：处理订单成交、取消、拒单等事件。
# 5. 日志输出：记录买卖时机和成交价格，便于回测复盘。

class TestStrategy(bt.Strategy):
    """示例策略：连续下跌两日后买入，持仓 5 日后卖出。"""

    def log(self, txt, dt=None):
        ''' 日志函数：输出当前日期及策略信息 '''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已经提交或被接受，暂不处理后续逻辑
            return

        # 订单完成时输出成交信息
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # 无挂单状态，允许下一根 K 线继续发出新信号
        self.order = None

    def next(self):
        # 记录当前 K 线收盘价，便于后续分析
        self.log('Close, %.2f' % self.dataclose[0])

        # 如果有未完成订单，则本周期不再发出新订单
        if self.order:
            return

        # 当前无持仓时，判断是否发出买入信号
        if not self.position:

            # 连续两根 K 线收盘价下降，则建立买入单
            if self.dataclose[0] < self.dataclose[-1]:
                if self.dataclose[-1] < self.dataclose[-2]:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order = self.buy()

        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()