import backtrader as bt
from datetime import datetime
import pandas as pd


class ManualMovingAverageSignal(bt.Strategy):
    """记录买卖信号并模拟持仓状态的策略。

    该策略基于简单移动平均线生成买入/卖出信号，
    并将建议手数记录到 signals 列表中，供手工下单使用。
    """

    params = (
        ("maperiod", 20),
        ("max_cash_fraction", 0.5),
        ("lot_size", 100),
        ("ts_code", ""),
        ("stock_name", ""),
        ("signals", None),
    )

    def __init__(self):
        # 保存当前数据序列的收盘价引用
        self.close = self.datas[0].close
        # 计算简单移动平均线，用于买卖信号判断
        self.ma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.p.maperiod)
        # 当前正在处理的订单，如果存在则跳过重复下单
        self.order = None

    def next(self):
        # 如果当前还有未完成订单，则本周期不再发出新订单
        if self.order:
            return

        close_price = float(self.close[0])
        ma_value = float(self.ma[0])
        if pd.isna(close_price) or pd.isna(ma_value) or close_price <= 0:
            return

        if not self.position and close_price > ma_value:
            # 当无持仓且收盘价高于均线时触发买入信号
            shares = self._suggest_buy_size(close_price)
            if shares <= 0:
                self._record_signal(
                    action="WAIT",
                    shares=0,
                    close_price=close_price,
                    ma_value=ma_value,
                    reason="Buy signal, but available cash is not enough for one lot.",
                )
                return

            self._record_signal(
                action="BUY",
                shares=shares,
                close_price=close_price,
                ma_value=ma_value,
                reason=f"Close is above SMA{self.p.maperiod}; simulated position is empty.",
            )
            self.order = self.buy(size=shares)

        elif self.position and close_price < ma_value:
            # 当已有持仓且收盘价低于均线时触发卖出信号
            shares = int(self.position.size)
            self._record_signal(
                action="SELL",
                shares=shares,
                close_price=close_price,
                ma_value=ma_value,
                reason=f"Close is below SMA{self.p.maperiod}; simulated position exists.",
            )
            self.order = self.sell(size=shares)

    def notify_order(self, order):
        if order.status in (order.Submitted, order.Accepted):
            self.order = order
            return

        if order.status in (
            order.Completed,
            order.Canceled,
            order.Margin,
            order.Rejected,
        ):
            self.order = None

    def _suggest_buy_size(self, price: float) -> int:
        # 计算可用资金的最大买入量，并按最小交易单位取整
        budget = self.broker.getcash() * self.p.max_cash_fraction
        raw_shares = int(budget // price)
        return (raw_shares // self.p.lot_size) * self.p.lot_size

    def _record_signal(
        self,
        action: str,
        shares: int,
        close_price: float,
        ma_value: float,
        reason: str,
    ) -> None:
        if self.p.signals is None:
            return

        signal_date = self.datas[0].datetime.date(0).isoformat()
        self.p.signals.append(
            {
                "run_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "signal_date": signal_date,
                "manual_action_date": "next trading day",
                "ts_code": self.p.ts_code,
                "stock_name": self.p.stock_name,
                "action": action,
                "suggested_shares": shares,
                "reference_close": round(close_price, 4),
                "sma": round(ma_value, 4),
                "cash_before_signal": round(float(self.broker.getcash()), 2),
                "portfolio_value": round(float(self.broker.getvalue()), 2),
                "status": "manual_entry_required" if action in ("BUY", "SELL") else "watch_only",
                "reason": reason,
                "manual_checklist": (
                    "1. Open broker paper account; "
                    "2. Confirm code/action/shares; "
                    "3. Enter order manually; "
                    "4. Mark result in your trading journal."
                ),
            }
        )