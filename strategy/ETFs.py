
import backtrader as bt

class ETFStrategy(bt.Strategy):
    """ETF 策略
        
    
    示例：基于简单移动平均线的买卖信号。"""

    params = (
        ("maperiod", 20),  # 移动平均线周期
        ("max_cash_fraction", 0.5),  # 单次买入最多使用账户可用资金的比例
    )

    def __init__(self):
        self.ma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod
        )
        self.dataclose = self.datas[0].close
        self.order = None

    def next(self):
        if self.order:
            return  # 如果有未完成的订单，跳过当前 K 线

        cash = self.broker.getcash()
        price = self.datas[0].close[0]
        if price is None or price <= 0:
            return

        if not self.position:  # 如果当前没有持仓
            if self.datas[0].close[0] > self.ma[0]:  # 收盘价上穿均线，买入信号
                max_size = max(int((cash * self.p.max_cash_fraction) / price), 1)
                self.order = self.buy(size=max_size)
        else:  # 如果当前已有持仓
            if self.datas[0].close[0] < self.ma[0]:  # 收盘价下穿均线，卖出信号
                self.order = self.sell(size=self.position.size)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return  # 等待订单成交

        elif order.status in [order.Completed]:
            if order.isbuy():
                print(f"买入成交: {order.executed.price}, 成本: {order.executed.value}, 手续费: {order.executed.comm}")
            elif order.issell():
                print(f"卖出成交: {order.executed.price}, 成本: {order.executed.value}, 手续费: {order.executed.comm}")
            self.order = None  # 重置订单状态

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print("订单取消/保证金不足/拒绝")
            self.order = None  # 重置订单状态