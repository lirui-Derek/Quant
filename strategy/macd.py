"""策略层：定义 MACD 金叉/死叉交易策略。"""

import backtrader as bt


class MACDStrategy(bt.Strategy):
    """使用 MACD 指标做多空信号判断的策略。"""

    # 策略参数：
    # fast_period：快线 EMA 周期，默认 12
    # slow_period：慢线 EMA 周期，默认 26
    # signal_period：信号线 DEA 周期，默认 9
    # stop_loss：止损比例，默认 0.05 表示亏损 5% 平仓
    # take_profit：止盈比例，默认 0.10 表示盈利 10% 平仓
    params = (
        ("fast_period", 12),
        ("slow_period", 26),
        ("signal_period", 9),
        ("order_size", 500),
    )

    def __init__(self):
        # 创建 Backtrader 内置 MACD 指标。
        # MACD 会根据收盘价计算：
        # 1. macd：DIF 线，即快 EMA 与慢 EMA 的差值
        # 2. signal：DEA 线，即 DIF 的平滑信号线
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fast_period,
            period_me2=self.p.slow_period,
            period_signal=self.p.signal_period,
        )

        # 保存 MACD 主线、信号线和柱状图，方便 next() 中直接使用。
        self.macd_line = self.macd.lines.macd
        self.signal_line = self.macd.lines.signal
        self.macd_hist = self.macd_line - self.signal_line

        # 记录当前挂单。挂单未完成前不重复发出买卖指令。
        self.order = None
        # 记录买入成交价，用来计算持仓期间的止盈止损价位。
        self.entry_price = None

    def next(self):
        # 如果上一笔订单还在处理中，跳过当前 K 线，避免重复下单。
        if self.order:
            return

        # 金叉：MACD 上穿 Signal 线
        # 当前没有持仓时才考虑买入。
        if not self.position:
            if (
                # 当前 K 线 MACD 已经在 Signal 上方，
                # 上一根 K 线 MACD 还在 Signal 下方或持平，说明刚刚发生上穿。
                self.macd_line[0] > self.signal_line[0]
                and self.macd_line[-1] <= self.signal_line[-1]
            ):
                self.order = self.buy(size=self.p.order_size)
        # 死叉：MACD 下穿 Signal 线
        # 当前已有持仓时才考虑卖出平仓。
        else:
            if self._should_stop_loss():
                self.order = self.sell(size=self.p.order_size)
                return

            if self._should_take_profit():
                self.order = self.sell()
                return

            if (
                # 当前 K 线 MACD 已经在 Signal 下方，
                # 上一根 K 线 MACD 还在 Signal 上方或持平，说明刚刚发生下穿。
                self.macd_line[0] < self.signal_line[0]
                and self.macd_line[-1] >= self.signal_line[-1]
            ):
                self.order = self.sell()

    def _should_stop_loss(self):
        """判断当前价格是否触发止损。"""
        if self.entry_price is None or self.p.stop_loss is None:
            return False

        stop_price = self.entry_price * (1 - self.p.stop_loss)
        return self.data.close[0] <= stop_price

    def _should_take_profit(self):
        """判断当前价格是否触发止盈。"""
        if self.entry_price is None or self.p.take_profit is None:
            return False

        take_profit_price = self.entry_price * (1 + self.p.take_profit)
        return self.data.close[0] >= take_profit_price

    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.entry_price = order.executed.price
            elif order.issell():
                self.entry_price = None

        # 订单完成、取消或因保证金不足被拒绝后，清空挂单状态，
        # 允许后续 K 线继续产生新的交易信号。
        if order.status in (
            order.Completed,
            order.Canceled,
            order.Margin,
            order.Rejected,
        ):
            self.order = None
        
